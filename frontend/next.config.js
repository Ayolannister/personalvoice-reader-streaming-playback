/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    // Covers come from the local backend. The Next image optimizer fetches
    // them server-side, which breaks inside Docker (localhost there is the
    // frontend container, not the backend). Optimization buys nothing for a
    // single-user local app, so serve the originals directly.
    unoptimized: true,
    // Book covers and voice avatars are served locally from the backend/MinIO in later milestones.
    remotePatterns: [
      { protocol: "http", hostname: "localhost", port: "8000" },
      { protocol: "http", hostname: "127.0.0.1", port: "8000" },
    ],
  },
};

module.exports = nextConfig;
