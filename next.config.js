/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Next.js will automatically detect src/pages directory
  pageExtensions: ['tsx', 'ts', 'jsx', 'js'],
  env: {
    REACT_APP_API_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig



