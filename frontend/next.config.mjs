/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enforces React best practices and lifecycle checks in development
  reactStrictMode: true,

  // Optimizes the production build into a minimal standalone bundle for Docker
  output: "standalone",

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
