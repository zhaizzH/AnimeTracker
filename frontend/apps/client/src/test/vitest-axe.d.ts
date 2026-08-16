// vitest-axe 0.1.0 的 extend-expect.d.ts 针对的是旧版 vitest 的 Vi.Assertion，
// 在 vitest 2.x 下不会生效；这里显式增强 vitest 的 Assertion（与 jest-dom 相同的做法）。
// 运行时匹配器由 src/test/setup.ts 的 expect.extend 注册；此处仅补全类型。
import 'vitest';

declare module 'vitest' {
  interface Assertion<T> {
    toHaveNoViolations(): void;
  }
}
