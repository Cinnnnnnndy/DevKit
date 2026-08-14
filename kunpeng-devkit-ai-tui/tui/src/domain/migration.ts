import type { Architecture, EvidenceReference, IsoDateTime, TaskId } from "./common";

export type PlanStepStatus = "pending" | "running" | "paused" | "completed" | "failed" | "skipped";

export interface PlanStep {
  readonly id: string;
  readonly title: string;
  readonly description: string;
  readonly status: PlanStepStatus;
  readonly tool?: string;
  readonly durationMs?: number;
}

export interface MigrationPlan {
  readonly taskId: TaskId;
  readonly goal: string;
  readonly sourcePath: string;
  readonly sourceArchitecture: Architecture;
  readonly targetArchitecture: Architecture;
  readonly version: number;
  readonly estimatedDurationMs: number;
  readonly steps: readonly PlanStep[];
}

export interface CreateMigrationPlanRequest {
  readonly prompt: string;
  readonly sourcePath: string;
  readonly sourceArchitecture?: Architecture;
  readonly targetArchitecture?: Architecture;
}

export interface EditablePlanStep {
  readonly id: string;
  readonly title: string;
  readonly enabled: boolean;
}

export interface UpdateMigrationPlanRequest {
  readonly taskId: TaskId;
  readonly expectedVersion: number;
  readonly steps: readonly EditablePlanStep[];
}

export interface ConfigurationField {
  readonly key: string;
  readonly label: string;
  readonly kind: "path" | "integer" | "secret" | "text";
  readonly required: boolean;
  readonly sensitive: boolean;
  readonly defaultValue?: string | number;
  readonly hint?: string;
}

export interface ConfigurationRequirement {
  readonly taskId: TaskId;
  readonly resumeToken: string;
  readonly pausedStepId: string;
  readonly reason: string;
  readonly fields: readonly ConfigurationField[];
  readonly canSkip: boolean;
}

export interface ResolveConfigurationRequest {
  readonly taskId: TaskId;
  readonly resumeToken: string;
  readonly values: Readonly<Record<string, string | number>>;
  readonly skip: boolean;
}

export interface ConfigurationResolution {
  readonly taskId: TaskId;
  readonly resumedStepId: string;
  readonly status: "resumed" | "skipped";
}

export type IssueSeverity = "critical" | "warning" | "info";

export interface CompatibilityIssue {
  readonly id: string;
  readonly severity: IssueSeverity;
  readonly title: string;
  readonly file: string;
  readonly line: number;
  readonly autoFixable: boolean;
  readonly evidence: readonly EvidenceReference[];
}

export interface FileRisk {
  readonly path: string;
  readonly risk: number;
  readonly issueCount: number;
}

export interface MigrationReport {
  readonly taskId: TaskId;
  readonly compatibilityScore: number;
  readonly criticalCount: number;
  readonly warningCount: number;
  readonly autoFixableCount: number;
  readonly files: readonly FileRisk[];
  readonly issues: readonly CompatibilityIssue[];
  readonly generatedAt: IsoDateTime;
}

export interface CompatibilityAnalysisRequest {
  readonly taskId: TaskId;
  readonly includeBuildScripts: boolean;
}

export interface DiffLine {
  readonly kind: "context" | "addition" | "deletion";
  readonly oldLine?: number;
  readonly newLine?: number;
  readonly content: string;
}

export type PatchDecision = "pending" | "accepted" | "rejected";

export interface MigrationPatch {
  readonly id: string;
  readonly issueId: string;
  readonly file: string;
  readonly summary: string;
  readonly impact: string;
  readonly decision: PatchDecision;
  readonly lines: readonly DiffLine[];
  readonly evidence: readonly EvidenceReference[];
}

export interface PatchReviewBundle {
  readonly taskId: TaskId;
  readonly patches: readonly MigrationPatch[];
  readonly acceptedCount: number;
  readonly rejectedCount: number;
  readonly pendingCount: number;
}

export interface ReviewPatchRequest {
  readonly taskId: TaskId;
  readonly patchId: string;
  readonly decision: Exclude<PatchDecision, "pending">;
}
