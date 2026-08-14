import type { EvidenceReference, MetricSnapshot, TaskId } from "./common";

export interface TraceSpan {
  readonly id: string;
  readonly label: string;
  readonly startMs: number;
  readonly durationMs: number;
  readonly intensity: number;
}

export interface TraceLane {
  readonly id: string;
  readonly label: string;
  readonly spans: readonly TraceSpan[];
}

export interface PerformanceBaseline {
  readonly taskId: TaskId;
  readonly bottleneck: "compute-bound" | "memory-bound" | "io-bound" | "balanced";
  readonly metrics: MetricSnapshot;
  readonly hbmUtilizationPercent: number;
  readonly npuUtilizationPercent: number;
  readonly trace: readonly TraceLane[];
  readonly evidence: readonly EvidenceReference[];
}

export interface TuningChange {
  readonly key: string;
  readonly before: string;
  readonly after: string;
  readonly reason: string;
}

export interface TuningPlan {
  readonly id: string;
  readonly name: string;
  readonly recommended: boolean;
  readonly description: string;
  readonly metrics: MetricSnapshot;
  readonly changes: readonly TuningChange[];
  readonly tradeoffs: readonly string[];
}

export interface TuningComparison {
  readonly taskId: TaskId;
  readonly baseline: MetricSnapshot;
  readonly plans: readonly TuningPlan[];
}

export interface ApplyTuningPlanRequest {
  readonly taskId: TaskId;
  readonly planId: string;
}

export interface TuningApplication {
  readonly taskId: TaskId;
  readonly planId: string;
  readonly before: MetricSnapshot;
  readonly after: MetricSnapshot;
  readonly changedFiles: readonly string[];
}

export interface ScenarioProfile {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  readonly recommendedFor: readonly string[];
  readonly estimatedDurationMs: number;
}

export interface RunScenarioProfileRequest {
  readonly taskId: TaskId;
  readonly profileId: string;
}

export interface ScenarioProfileResult {
  readonly taskId: TaskId;
  readonly profileId: string;
  readonly status: "passed" | "needs-review";
  readonly metrics: MetricSnapshot;
  readonly observations: readonly string[];
}
