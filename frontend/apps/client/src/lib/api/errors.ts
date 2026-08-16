export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly code?: number,
    readonly requestId?: string,
  ) { super(message); }
}
