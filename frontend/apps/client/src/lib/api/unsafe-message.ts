/** 诊断泄漏过滤器：堆栈痕迹视为不安全，替换为通用兜底文案。适配器与路由错误边界共用，勿在别处复制。 */
export const UNSAFE_MESSAGE_FALLBACK = '服务暂时不可用，请稍后重试';

const UNSAFE_MESSAGE_RE = /java\.lang\.|Traceback| at top\./;

export function isUnsafeMessage(message: string): boolean {
  return UNSAFE_MESSAGE_RE.test(message);
}
