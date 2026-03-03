import type { NextConfig } from "next";

const API_URL = process.env.API_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Habilitar standalone output para optimizar la imagen Docker
  output: "standalone",

  // Permitir imágenes de mapas base
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "*.basemaps.cartocdn.com" },
    ],
  },

  // Proxy /api/v1/* hacia el backend para evitar CORS en desarrollo
  // y como fallback en producción si no se usa NEXT_PUBLIC_API_URL
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
