import type { NextConfig } from "next";

const isProd = process.env.VERCEL === "1";

const nextConfig: NextConfig = {
  async rewrites() {
    if (isProd) {
      return [];
    }
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
