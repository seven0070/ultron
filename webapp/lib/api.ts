// Thin fetch wrapper around Monad's FastAPI backend (/api/monad/* → :8765)

export const API = '/api/monad'

async function req<T = any>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!r.ok) {
    const txt = await r.text().catch(() => '')
    throw new Error(`${r.status} ${r.statusText} — ${txt.slice(0, 200)}`)
  }
  return r.json()
}

export const monad = {
  health:   () => req('/health'),
  info:     () => req('/info'),
  models:   () => req('/models'),
  organs:   () => req('/organs'),
  tools:    () => req('/tools'),
  policy:   (limit = 50) => req(`/policy/audit?limit=${limit}`),

  ask: (prompt: string, opts: { strategy?: string; cognition?: boolean; fusion?: boolean } = {}) =>
    req('/ask', { method: 'POST',
      body: JSON.stringify({ prompt, ...opts }) }),

  fuse: (prompt: string, mode: 'auto'|'chain'|'ensemble'|'logits' = 'auto', max_tokens = 1024) =>
    req('/fuse', { method: 'POST', body: JSON.stringify({ prompt, mode, max_tokens }) }),

  remember: (text: string, kind = 'user_note', tag = 'chat') =>
    req('/memory/remember', { method: 'POST', body: JSON.stringify({ text, kind, tag }) }),

  recall:   (query: string, top_k = 5) =>
    req('/memory/recall', { method: 'POST', body: JSON.stringify({ query, top_k }) }),

  runTool:  (id: string, kwargs: Record<string, any>) =>
    req(`/tools/${id}`, { method: 'POST', body: JSON.stringify({ kwargs }) }),

  evolveHistory: () => req('/evolve/history'),
  evolvePropose: (goal: string, target: string, zone = 'plugins') =>
    req('/evolve/propose', { method: 'POST',
      body: JSON.stringify({ goal, target, zone }) }),

  learn: (source: string, kind: 'url'|'text'|'repo' = 'text') =>
    req('/learn', { method: 'POST', body: JSON.stringify({ source, kind }) }),
}
