export type TaskId = string;
export type SessionId = string;
export type IsoDateTime = string;
export type Architecture = "x86_64" | "aarch64";
export type TaskStatus = "idle" | "running" | "paused" | "completed" | "failed" | "cancelled";

export interface EvidenceReference {
  readonly id: string;
  readonly kind: "source" | "log" | "knowledge" | "manual" | "metric";
  readonly label: string;
  readonly locator: string;
  readonly excerpt?: string;
}

export interface MetricSnapshot {
  readonly qps: number;
  readonly p99LatencyMs: number;
  readonly cpuPercent: number;
  readonly memoryGiB: number;
}
