import { expect, test } from 'vitest';
import { SHARED_SENTINEL } from './index';
test('shared 可被解析', () => expect(SHARED_SENTINEL).toBe('shared-ok'));
