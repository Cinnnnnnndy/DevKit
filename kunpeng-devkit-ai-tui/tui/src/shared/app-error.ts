export type AppErrorKind =
  | "cancelled"
  | "invalid-input"
  | "not-found"
  | "conflict"
  | "capability-missing"
  | "offline"
  | "timeout"
  | "unexpected";

export interface AppError {
  readonly kind: AppErrorKind;
  readonly code: string;
  readonly message: string;
  readonly retryable: boolean;
  readonly details?: Readonly<Record<string, string | number | boolean>>;
}

export function createAppError(
  kind: AppErrorKind,
  code: string,
  message: string,
  retryable: boolean,
  details?: Readonly<Record<string, string | number | boolean>>,
): AppError {
  return details === undefined
    ? { kind, code, message, retryable }
    : { kind, code, message, retryable, details };
}

export const cancelledError = (): AppError =>
  createAppError("cancelled", "operation.cancelled", "操作已取消", false);
