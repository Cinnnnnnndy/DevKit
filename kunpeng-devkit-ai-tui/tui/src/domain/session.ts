import type { IsoDateTime, MetricSnapshot, SessionId, TaskId } from "./common";

export interface SessionSummary {
  readonly sessionId: SessionId;
  readonly taskId: TaskId;
  readonly title: string;
  readonly fixedIssueCount: number;
  readonly manualReviewCount: number;
  readonly buildStatus: "passed" | "failed" | "skipped";
  readonly baseline: MetricSnapshot;
  readonly finalMetrics: MetricSnapshot;
  readonly modifiedFiles: readonly string[];
  readonly pendingActions: readonly string[];
  readonly generatedAt: IsoDateTime;
}

export interface ExportSessionReportRequest {
  readonly summary: SessionSummary;
  readonly format: "markdown" | "json";
  readonly destinationPath: string;
}

export interface ExportedReport {
  readonly destinationPath: string;
  readonly byteLength: number;
  readonly format: "markdown" | "json";
}
