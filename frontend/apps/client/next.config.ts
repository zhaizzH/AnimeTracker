import type { NextConfig } from 'next';

/** 封面图宿主（与后端/组件测试约定一致），next/image 与 CSP 同时放行。 */
const COVER_HOSTS = ['lain.bgm.tv'];

const nextConfig: NextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  images: {
    // 自托管静态资源（'self'） + 配置的封面宿主；尺寸由组件内的 sizes 属性约束。
    remotePatterns: COVER_HOSTS.map((hostname) => ({ protocol: 'https', hostname })),
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "base-uri 'self'",
              "form-action 'self'",
              "frame-ancestors 'self'",
              "object-src 'none'",
              "img-src 'self' data: https://lain.bgm.tv",
              "font-src 'self' data:",
              "script-src 'self' 'unsafe-inline'",
              "style-src 'self' 'unsafe-inline'",
              "connect-src 'self'",
            ].join('; '),
          },
        ],
      },
    ];
  },
};

export default nextConfig;
