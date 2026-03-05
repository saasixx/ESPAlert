import type { NextConfig } from "next";
import path from "node:path";

const API_URL = process.env.API_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  turbopack: {
    root: path.resolve(__dirname, "../.."),
  },

  // standalone output only for Docker (Vercel uses its own build system)
  ...(process.env.VERCEL ? {} : { output: "standalone" }),

  // Allow map tile images
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "*.basemaps.cartocdn.com" },
    ],
  },

  // Proxy /api/v1/* to the backend to avoid CORS in development
  // and as a fallback in production if NEXT_PUBLIC_API_URL is not used
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${API_URL}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
