/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enforces React best practices and lifecycle checks in development
  reactStrictMode: true,

  // Only use standalone output for Docker containers; Vercel handles deployment natively
  output: process.env.VERCEL ? undefined : "standalone",

  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },

  // Environment variable fallbacks for client-side API calls
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  },

  // In development, rewrite /api requests directly to the FastAPI backend
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
