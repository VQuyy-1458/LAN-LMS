import type { NextConfig } from "next";

const apiUpstream = process.env.API_UPSTREAM;

const nextConfig: NextConfig = {
  async rewrites() {
    if (!apiUpstream) {
      return [];
    }

    return [
      {
        source: "/api/:path*",
        destination: `${apiUpstream}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;