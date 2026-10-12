import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach } from 'vitest';

// vitest 未开启 globals，@testing-library/react 的自动 cleanup 不会注册；
// 不显式清理会导致 DOM 跨用例累积，使角色查询出现重复匹配。
afterEach(() => cleanup());

// jsdom 未实现 matchMedia；主题解析（resolveMode）与主题桥依赖它。
if (typeof window !== 'undefined' && !window.matchMedia) {
  window.matchMedia = ((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => undefined,
    removeListener: () => undefined,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
}

// jsdom 未实现 PointerEvent API，radix-ui 的 DropdownMenu/Tooltip 会直接调用它们。
// 只补 radix 实际用到的最小集合，避免引入额外 polyfill 依赖。
if (typeof Element !== 'undefined') {
  const proto = Element.prototype as unknown as Record<string, unknown>;
  proto.hasPointerCapture ??= () => false;
  proto.setPointerCapture ??= () => {};
  proto.releasePointerCapture ??= () => {};
  proto.scrollIntoView ??= () => {};
}

// radix 的尺寸测量依赖 ResizeObserver。
if (typeof globalThis.ResizeObserver === 'undefined') {
  globalThis.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  } as unknown as typeof ResizeObserver;
}
