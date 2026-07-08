// Natural-language command parser.
//
// The chat input isn't just "prompt → LLM". If the user says
//   "integrate https://github.com/foo/bar"
//   "learn this: <paste>"
//   "evolve: add a bluetooth scanner plugin"
//   "remember: my API key rotation is every 90 days"
//   "run tool filesystem read notes.txt"
//   "fuse: explain quantum entanglement"
// we detect the intent and route to the right backend action.

export type Command =
  | { kind: 'ask';       prompt: string; cognition?: boolean }
  | { kind: 'fuse';      prompt: string; mode: 'auto'|'chain'|'ensemble'|'logits' }
  | { kind: 'learn';     source: string; sourceKind: 'url'|'text'|'repo' }
  | { kind: 'integrate'; url: string }
  | { kind: 'evolve';    goal: string; target?: string; zone?: string }
  | { kind: 'remember';  text: string }
  | { kind: 'recall';    query: string }
  | { kind: 'forget';    needle: string }
  | { kind: 'tool';      id: string; kwargs: Record<string, any> }
  | { kind: 'help' }

const URL_RE = /https?:\/\/[^\s]+/i

export function parseCommand(input: string): Command {
  const raw = input.trim()
  if (!raw) return { kind: 'help' }

  const lower = raw.toLowerCase()

  // --- Help -----------------------------------------------------------------
  if (['/help', 'help', '?'].includes(lower))
    return { kind: 'help' }

  // --- Fuse -----------------------------------------------------------------
  const fuseMatch = raw.match(/^\/?fuse(?:\s+(chain|ensemble|logits|auto))?[:\s]+(.+)/i)
  if (fuseMatch) {
    const mode = (fuseMatch[1] || 'auto').toLowerCase() as any
    return { kind: 'fuse', prompt: fuseMatch[2].trim(), mode }
  }

  // --- Learn (URL, text, or repo) ------------------------------------------
  const learnMatch = raw.match(/^\/?learn(?:\s+this)?[:\s]+(.+)/is)
  if (learnMatch) {
    const source = learnMatch[1].trim()
    const looksLikeRepo =
      /^https?:\/\/(github|gitlab|bitbucket)\.com\//i.test(source) ||
      /^git@/.test(source) || /\.git($|\s)/.test(source)
    const looksLikeUrl = URL_RE.test(source) && !looksLikeRepo
    const sourceKind: 'url'|'text'|'repo' =
      looksLikeRepo ? 'repo' : looksLikeUrl ? 'url' : 'text'
    return { kind: 'learn', source, sourceKind }
  }

  // --- Integrate (github repo / package / mcp server) ----------------------
  const integrateMatch = raw.match(/^\/?integrate\s+(.+)/is)
  if (integrateMatch) {
    const arg = integrateMatch[1].trim()
    const url = arg.match(URL_RE)?.[0] || arg
    return { kind: 'integrate', url }
  }

  // --- Evolve --------------------------------------------------------------
  const evolveMatch = raw.match(/^\/?evolve(?:\s+(?:this|it))?[:\s]+(.+)/is)
  if (evolveMatch) {
    const rest = evolveMatch[1].trim()
    // Optional "into <target>" for explicit target file
    const intoMatch = rest.match(/^(.+?)\s+into\s+(\S+)$/is)
    if (intoMatch)
      return { kind: 'evolve', goal: intoMatch[1].trim(), target: intoMatch[2].trim() }
    return { kind: 'evolve', goal: rest }
  }

  // --- Memory --------------------------------------------------------------
  const rememberMatch = raw.match(/^\/?remember[:\s]+(.+)/is)
  if (rememberMatch) return { kind: 'remember', text: rememberMatch[1].trim() }

  const recallMatch = raw.match(/^\/?recall[:\s]+(.+)/is)
  if (recallMatch) return { kind: 'recall', query: recallMatch[1].trim() }

  const forgetMatch = raw.match(/^\/?forget[:\s]+(.+)/is)
  if (forgetMatch) return { kind: 'forget', needle: forgetMatch[1].trim() }

  // --- Tool ----------------------------------------------------------------
  //   "/tool <id> <op?> <key=value> ..."
  //   "run tool filesystem read notes.txt"
  const toolMatch = raw.match(/^(?:\/tool|run\s+tool)\s+(\S+)\s*(.*)/is)
  if (toolMatch) {
    const id = toolMatch[1]
    const argStr = toolMatch[2] || ''
    return { kind: 'tool', id, kwargs: parseToolArgs(argStr) }
  }

  // --- Cognition prefix -----------------------------------------------------
  if (lower.startsWith('/cog ') || lower.startsWith('cognition ')) {
    return { kind: 'ask', prompt: raw.replace(/^(\/cog|cognition)\s+/i, ''),
             cognition: true }
  }

  // --- Default: it's a normal question --------------------------------------
  return { kind: 'ask', prompt: raw }
}

function parseToolArgs(s: string): Record<string, any> {
  const out: Record<string, any> = {}
  // key=value pairs
  const kvRe = /(\w+)=("([^"]*)"|'([^']*)'|(\S+))/g
  let m: RegExpExecArray | null
  const consumed: [number, number][] = []
  while ((m = kvRe.exec(s))) {
    const key = m[1]
    const val = m[3] ?? m[4] ?? m[5]
    out[key] = val
    consumed.push([m.index, m.index + m[0].length])
  }
  // Leftover positional args -> collect into "positional"
  let remainder = s
  for (const [a, b] of consumed.reverse())
    remainder = remainder.slice(0, a) + remainder.slice(b)
  remainder = remainder.trim()
  if (remainder) {
    const parts = remainder.split(/\s+/)
    // Heuristic mapping for common tools
    if (parts.length && !('op' in out)) out.op = parts.shift()
    if (parts.length && !('path' in out) && !('command' in out) &&
        !('code' in out) && !('url' in out))
      out.path = parts.join(' ')
  }
  return out
}
