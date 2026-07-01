/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
  images: {
    remotePatterns: [
      // Local development
      { protocol: 'http', hostname: 'localhost' },
      // Render-hosted backend (production)
      { protocol: 'https', hostname: '**.onrender.com' },
    ],
  },
};

module.exports = nextConfig;
