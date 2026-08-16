import '@testing-library/jest-dom/vitest';
import { expect } from 'vitest';
import * as axeMatchers from 'vitest-axe/matchers';

// vitest-axe 的 toHaveNoViolations 匹配器，供 accessibility.test.tsx 使用。
expect.extend(axeMatchers);
