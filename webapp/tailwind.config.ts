import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './app/**/*.{ts,tsx,mdx}',
    './components/**/*.{ts,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Monad palette — deep space + neon
        bg: {
          DEFAULT: '#0a0b14',
          soft: '#111327',
          card: '#171a30',
          hover: '#1e2242',
        },
        border: { DEFAULT: '#252a4a', soft: '#1e2242' },
        text: {
          DEFAULT: '#e6e8f5',
          soft: '#a5aad0',
          muted: '#666a8a',
        },
        accent: {
          purple: '#a78bfa',
          pink: '#f472b6',
          blue: '#60a5fa',
          cyan: '#22d3ee',
          green: '#34d399',
          amber: '#fbbf24',
          red: '#f87171',
        },
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace'],
      },
      backgroundImage: {
        'monad-radial': 'radial-gradient(ellipse at top, rgba(167,139,250,0.15), transparent 60%), radial-gradient(ellipse at bottom right, rgba(96,165,250,0.10), transparent 55%)',
        'monad-gradient': 'linear-gradient(135deg, #a78bfa 0%, #f472b6 50%, #60a5fa 100%)',
      },
      animation: {
        'pulse-glow': 'pulse-glow 3s ease-in-out infinite',
        'shimmer': 'shimmer 2.5s linear infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(167,139,250,0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(167,139,250,0.6)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-8px)' },
        },
      },
    },
  },
  plugins: [],
}
export default config
