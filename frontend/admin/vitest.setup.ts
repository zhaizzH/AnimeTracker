import '@testing-library/jest-dom/vitest';

// jsdom 未实现 PointerEvent API，radix-ui 的 Select/Switch 会直接调用它们。
// 只补 radix 实际用到的最小集合，避免引入额外 polyfill 依赖。
if (typeof Element !== 'undefined') {
  const proto = Element.prototype as unknown as Record<string, unknown>;
  proto.hasPointerCapture ??= () => false;
  proto.setPointerCapture ??= () => {};
  proto.releasePointerCapture ??= () => {};
  proto.scrollIntoView ??= () => {};
}
