import { useSyncExternalStore } from 'react';

// Agent 发起导航时浮层的两个开关。模块级而非 React context：
// 调用方是 hook 回调（非组件上下文），拿不到 context；也不引新状态库。
//
// 调用顺序固定为 markAgentNavigation() → navigate() → showNavHint(label)。
// 反了的话 AIAssistantFloat 的 location.key effect 会先跑，面板被关掉。

// 一次性标记：只为「紧接着的那一次路由变化」放行，用后立即复位。
// 不复位的话，用户之后手动点导航链接也会被误当成 agent 导航，面板不再关闭。
let pendingAgentNavigation = false;

export function markAgentNavigation(): void {
  pendingAgentNavigation = true;
}

/** 消费一次性标记：返回 true 表示本次路由变化由 agent 发起，并立即复位。 */
export function consumeAgentNavigation(): boolean {
  const marked = pendingAgentNavigation;
  pendingAgentNavigation = false;
  return marked;
}

// 系统提示是本地瞬时 UI 状态，不进 useAgentChat 的 messages（那是会话历史，
// 会持久化到后端）；刷新即消失，不补。面板关闭时也保留，下次打开显示。
// 只有一个槽位，连续两次导航只显示最后一次，天然不累积。
let navHint: string | null = null;
const listeners = new Set<() => void>();

export function showNavHint(label: string): void {
  navHint = label;
  listeners.forEach((listener) => listener());
}

/** 用户手动导航时作废提示：留着的话用户跳走后仍看到上一条「已跳转到」，属过期假信息。 */
export function clearNavHint(): void {
  if (navHint === null) return;
  navHint = null;
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function getSnapshot(): string | null {
  return navHint;
}

/** 订阅最近一条导航提示：面板关闭期间到达的提示会在下次打开时补显示。 */
export function useNavHint(): string | null {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
