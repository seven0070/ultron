/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Proxy /api/monad/* -> the Python FastAPI backend on :8765
  async rewrites() {
    const backend = process.env.NEXT_PUBLIC_MONAD_API || 'http://127.0.0.1:8765'
    return [
      { source: '/api/monad/:path*', destination: `${backend}/:path*` },
    ]
  },
  // Allow serving from any localhost port in dev
  experimental: { serverActions: { allowedOrigins: ['localhost:3000', '127.0.0.1:3000'] } },
}
export default nextConfig
