/** @type {import('next').NextConfig} */
const isGitHubPages = process.env.GITHUB_PAGES === "true";
const repoName = "/ai-document-intelligence-assistant";

const nextConfig = {
  reactStrictMode: true,
  output: "export",
  basePath: isGitHubPages ? repoName : "",
  assetPrefix: isGitHubPages ? repoName : "",
  images: {
    unoptimized: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "https://ai-document-intelligence-assistant-1.onrender.com",
  },
};

module.exports = nextConfig;
