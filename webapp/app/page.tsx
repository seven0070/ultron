'use client'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowRight, Brain, Sparkles, Zap, Shield, Cpu, GitBranch,
         Layers, Network, Lock } from 'lucide-react'

export default function Landing() {
  return (
    <main className="min-h-screen">
      <Nav />
      <Hero />
      <Stats />
      <Features />
      <Architecture />
      <CTA />
      <Footer />
    </main>
  )
}

function Nav() {
  return (
    <header className="fixed top-0 inset-x-0 z-50 glass border-b border-border-soft">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          <span className="font-semibold tracking-tight text-lg gradient-text">Monad</span>
          <span className="text-xs text-text-muted ml-1">v0.8</span>
        </Link>
        <nav className="hidden md:flex gap-8 text-sm text-text-soft">
          <a href="#features" className="hover:text-text-DEFAULT">Features</a>
          <a href="#architecture" className="hover:text-text-DEFAULT">Architecture</a>
          <a href="https://github.com/YOUR_USERNAME/Monad-Ultron"
             target="_blank" rel="noreferrer" className="hover:text-text-DEFAULT">GitHub</a>
        </nav>
        <Link href="/chat" className="btn-primary">
          Launch Monad <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </header>
  )
}

function Hero() {
  return (
    <section className="pt-40 pb-24 px-6">
      <div className="max-w-5xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full
                          border border-border text-xs text-text-soft mb-8">
            <span className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
            139 tests passing · self-improving · offline-first
          </div>

          <h1 className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.1] mb-6">
            The portable AI<br />
            <span className="gradient-text">that thinks like a mind.</span>
          </h1>

          <p className="max-w-2xl mx-auto text-lg text-text-soft mb-10">
            Monad is a cognitive architecture — <span className="text-text-DEFAULT">82 specialized organs</span>,
            multi-model fusion, and self-improvement — that runs entirely on your USB.
            No cloud. No lock-in. Just intelligence you own.
          </p>

          <div className="flex flex-wrap gap-3 justify-center">
            <Link href="/chat" className="btn-primary text-base px-6 py-3">
              Start thinking together <ArrowRight className="w-5 h-5" />
            </Link>
            <a href="#features" className="btn-outline text-base px-6 py-3">
              How it works
            </a>
          </div>
        </motion.div>

        {/* Animated orb */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1, delay: 0.3 }}
          className="mt-16 relative w-72 h-72 mx-auto"
        >
          <div className="absolute inset-0 rounded-full bg-monad-gradient opacity-20 blur-3xl animate-pulse-glow" />
          <div className="absolute inset-8 rounded-full bg-monad-gradient opacity-30 blur-2xl animate-float" />
          <div className="absolute inset-0 flex items-center justify-center text-8xl">🧠</div>
        </motion.div>
      </div>
    </section>
  )
}

function Stats() {
  const stats = [
    { value: '82', label: 'Cognitive organs', accent: 'text-accent-purple' },
    { value: '9', label: 'Architecture layers', accent: 'text-accent-pink' },
    { value: '3+', label: 'LLMs fused as one', accent: 'text-accent-blue' },
    { value: '100%', label: 'Runs offline', accent: 'text-accent-green' },
  ]
  return (
    <section className="py-16 px-6 border-y border-border-soft">
      <div className="max-w-6xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6">
        {stats.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: i * 0.1 }} viewport={{ once: true }}
            className="text-center"
          >
            <div className={`text-4xl md:text-5xl font-bold ${s.accent}`}>{s.value}</div>
            <div className="text-sm text-text-muted mt-1">{s.label}</div>
          </motion.div>
        ))}
      </div>
    </section>
  )
}

function Features() {
  const items = [
    { icon: Brain,     title: '82 Cognitive Organs',
      body: 'Newton, Shannon, Taleb, CRISPR, octopus, slime mold — each organ contributes a specialized lens.' },
    { icon: Network,   title: 'Multi-Model Fusion',
      body: 'Three LLMs collaborate as one — sequential refinement, token voting, or true logit-level fusion.' },
    { icon: GitBranch, title: 'Self-Improving',
      body: 'Ask it to add a plugin, tool, or capability. It proposes, tests, and only applies with your approval.' },
    { icon: Layers,    title: '9-Layer Architecture',
      body: 'Perception → Memory → Reasoning → Executive → Organs → Self-Model → Adaptation → Action.' },
    { icon: Lock,      title: 'Local-First & Portable',
      body: 'Everything runs on a 128 GB USB. Optional cloud tier when you want it, off when you don\'t.' },
    { icon: Shield,    title: 'Approval-Gated',
      body: 'Every filesystem write, tool call, and self-modification passes through a policy gate with audit trail.' },
    { icon: Cpu,       title: 'Real Memory',
      body: 'SQLite + vector index + RRF hybrid retrieval — remembers what you talked about, forgets what you tell it to.' },
    { icon: Zap,       title: 'Speculative Decoding',
      body: '2–3× faster inference via draft models, KV cache quantization, and Flash Attention.' },
    { icon: Sparkles,  title: 'MCP-Native',
      body: 'Every organ is exposable as an MCP tool. Talks to Claude, Cursor, and any MCP-compatible client.' },
  ]
  return (
    <section id="features" className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Everything a mind should have.
          </h2>
          <p className="text-lg text-text-soft max-w-2xl mx-auto">
            Not a wrapper. Not a chatbot. A complete cognitive OS.
          </p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: i * 0.05 }} viewport={{ once: true }}
              className="glass rounded-xl p-6 hover:border-accent-purple/50 transition"
            >
              <div className="w-10 h-10 rounded-lg bg-monad-gradient/20 flex items-center
                              justify-center mb-4">
                <f.icon className="w-5 h-5 text-accent-purple" />
              </div>
              <h3 className="font-semibold text-lg mb-2">{f.title}</h3>
              <p className="text-sm text-text-soft leading-relaxed">{f.body}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

function Architecture() {
  return (
    <section id="architecture" className="py-24 px-6 bg-bg-soft/30">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            9 layers, <span className="gradient-text">one mind</span>.
          </h2>
          <p className="text-lg text-text-soft">
            Every request flows through the full stack — cognition first, LLMs second.
          </p>
        </div>
        <div className="glass rounded-2xl p-8 font-mono text-sm">
          <pre className="text-text-soft leading-relaxed overflow-x-auto whitespace-pre">
{`  ┌─────────────────────────────────────────────┐
  │  1. Perception     normalize input           │
  │  2. Memory         SQLite + vector + RRF     │
  │  3. Learning       feedback & reinforcement  │
  │  4. Reasoning      model router + reflexion  │
  │  5. Executive      weighted-vote decisions   │
  │  6. Organs         82 specialists consulted  │
  │  7. Self-Model     metacognition graph       │
  │  8. Adaptation     controlled evolution      │
  │  9. Action         tool use + output         │
  └────────────────────┬────────────────────────┘
                       │
                       ▼
              ┌────────────────────┐
              │  Fusion Engine     │
              │  chain·vote·logits │
              └────────────────────┘
                       │
                       ▼
              ONE unified answer`}
          </pre>
        </div>
      </div>
    </section>
  )
}

function CTA() {
  return (
    <section className="py-24 px-6">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-4xl md:text-5xl font-bold mb-6">
          Your AI. Your USB. <span className="gradient-text">Your rules.</span>
        </h2>
        <p className="text-lg text-text-soft mb-10 max-w-xl mx-auto">
          Plug in. Chat. Ask it to learn new things, integrate new tools,
          evolve new plugins — Monad grows with you.
        </p>
        <Link href="/chat" className="btn-primary text-base px-8 py-4">
          Open Monad <ArrowRight className="w-5 h-5" />
        </Link>
      </div>
    </section>
  )
}

function Footer() {
  return (
    <footer className="py-12 px-6 border-t border-border-soft">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-sm text-text-muted">
          <span>🧠</span>
          <span>Monad-Ultron · MIT · <a href="https://github.com/YOUR_USERNAME/Monad-Ultron"
                                       target="_blank" rel="noreferrer"
                                       className="hover:text-accent-purple">GitHub</a></span>
        </div>
        <div className="text-xs text-text-muted">
          Portable local AI · offline-first · self-improving · MCP-native
        </div>
      </div>
    </footer>
  )
}
