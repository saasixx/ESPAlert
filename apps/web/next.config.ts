import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Habilitar standalone output para optimizar la imagen Docker
  output: "standalone",

  // Permitir imágenes de mapas base
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "*.basemaps.cartocdn.com" },
    ],
  },
};

export default nextConfig;
