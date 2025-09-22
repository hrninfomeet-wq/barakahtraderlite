import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
        ],
      },
    ]
  },
  experimental: {
    serverActions: {
      allowedOrigins: ["*"]
    }
  },
  allowedDevOrigins: ["1b7fd467-acf6-4bd1-9040-93062c84f787-00-2w14iyh83mugu.sisko.replit.dev"]
};

export default nextConfig;
