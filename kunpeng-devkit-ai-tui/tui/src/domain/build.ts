import type { EvidenceReference, TaskId } from "./common";

export interface BuildRequest {
  readonly taskId: TaskId;
  readonly attempt: "initial" | "after-fix";
}

export interface BuildFailure {
  readonly code: string;
  readonly message: string;
  readonly file: string;
  readonly line: number;
}

interface BuildReportBase {
  readonly taskId: TaskId;
  readonly command: string;
  readonly durationMs: number;
  readonly output: readonly string[];
  readonly artifacts: readonly string[];
}

export type BuildReport =
  | (BuildReportBase & { readonly status: "passed"; readonly failure?: never })
  | (BuildReportBase & { readonly status: "failed"; readonly failure: BuildFailure });

export interface DiagnosisNode {
  readonly id: string;
  readonly label: string;
  readonly kind: "problem" | "evidence" | "root-cause" | "solution";
}

export interface DiagnosisEdge {
  readonly from: string;
  readonly to: string;
}

export interface BuildDiagnosis {
  readonly taskId: TaskId;
  readonly rootCause: string;
  readonly confidence: number;
  readonly nodes: readonly DiagnosisNode[];
  readonly edges: readonly DiagnosisEdge[];
  readonly evidence: readonly EvidenceReference[];
  readonly proposedFixId: string;
  readonly proposedFixSummary: string;
  readonly canApplyAutomatically: boolean;
}

export interface ApplyDiagnosisFixRequest {
  readonly taskId: TaskId;
  readonly fixId: string;
}

export interface AppliedFix {
  readonly taskId: TaskId;
  readonly fixId: string;
  readonly changedFiles: readonly string[];
  readonly nextAction: "rebuild";
}
