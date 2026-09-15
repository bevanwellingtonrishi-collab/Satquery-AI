import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // In development, proxy /api/* to the local FastAPI backend.
  // On Vercel, vercel.json rewrites handle this instead.
  async rewrites() {
    return process.env.VERCEL
      ? []
      : [
          {
            source: "/api/:path*",
            destination: "http://localhost:8000/api/:path*",
          },
        ];
  },
};

export default nextConfig;
