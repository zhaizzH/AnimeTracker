import { describe, expect, it } from 'vitest';
import config from '../../playwright.config';

type WebServer = {
  command: string;
  url?: string;
  env?: Record<string, string>;
};

function servers(): WebServer[] {
  return Array.isArray(config.webServer) ? config.webServer as unknown as WebServer[] : [];
}

describe('Playwright runtime configuration', () => {
  it('isolates the mock API from the normal local backend port', () => {
    const mockServer = servers().find((server) => server.command.includes('mock-server.mjs'));

    expect(mockServer?.url).toBe('http://127.0.0.1:18080/__health');
    expect(mockServer?.env).toMatchObject({ MOCK_PORT: '18080' });
  });

  it('injects the mock API URL only into the E2E Next.js process', () => {
    const nextServer = servers().find((server) => server.command.includes('pnpm build'));

    expect(nextServer?.env).toMatchObject({ BUSINESS_API_URL: 'http://127.0.0.1:18080' });
  });

});
