import type { NextConfig } from "next";

const isProd = process.env.VERCEL === "1";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    if (isProd) {
      return [];
    }
    return [
      {
        source: "/api/:path*",
        destination: "https://localhost:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
