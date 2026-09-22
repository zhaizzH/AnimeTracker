import { toast } from 'sonner';

// AntD `message.success` / `message.error` 的等价封装。文案由调用方原样传入，
// 保证迁移期间提示文案与 antd 版本逐字一致。
export function toastSuccess(message: string): void {
  toast.success(message);
}

export function toastError(message: string): void {
  toast.error(message);
}
