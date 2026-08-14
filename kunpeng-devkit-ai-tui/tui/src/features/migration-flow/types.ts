import type {
  AppliedFix,
  BuildDiagnosis,
  BuildReport,
  ConfigurationRequirement,
  ConfigurationResolution,
  EditablePlanStep,
  ExportedReport,
  FileRisk,
  MigrationPlan,
  MigrationReport,
  PatchDecision,
  PatchReviewBundle,
  PerformanceBaseline,
  ScenarioProfile,
  ScenarioProfileResult,
  SessionSummary,
  TuningApplication,
  TuningComparison,
  WorkspaceBootstrap,
} from "../../domain";
import type { AppError } from "../../shared";

export type MigrationAct = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

export type MigrationPhase =
  | "landing"
  | "plan"
  | "config"
  | "report"
  | "patch-review"
  | "build-failed"
  | "diagnosis"
  | "build-passed"
  | "baseline"
  | "tuning"
  | "profile"
  | "summary";

export type MigrationAsyncStatus = "idle" | "loading" | "ready" | "empty" | "error" | "cancelled";

export interface MigrationIntentDraft {
  readonly prompt: string;
  readonly sourcePath: string;
}

type MigrationFlowPosition =
  | { readonly phase: "landing"; readonly act: 1 }
  | { readonly phase: "plan"; readonly act: 2 }
  | { readonly phase: "config"; readonly act: 3 }
  | { readonly phase: "report"; readonly act: 4 }
  | { readonly phase: "patch-review"; readonly act: 5 }
  | {
      readonly phase: "build-failed" | "diagnosis" | "build-passed";
      readonly act: 6;
    }
  | { readonly phase: "baseline"; readonly act: 7 }
  | { readonly phase: "tuning"; readonly act: 8 }
  | { readonly phase: "profile"; readonly act: 9 }
  | { readonly phase: "summary"; readonly act: 10 };

interface MigrationFlowData {
  readonly asyncStatus: MigrationAsyncStatus;
  readonly pendingOperation: string | undefined;
  readonly error: AppError | undefined;
  readonly intent: MigrationIntentDraft;
  readonly workspace: WorkspaceBootstrap | undefined;
  readonly plan: MigrationPlan | undefined;
  readonly configuration: ConfigurationRequirement | undefined;
  readonly configurationResolution: ConfigurationResolution | undefined;
  readonly report: MigrationReport | undefined;
  readonly selectedRiskFile: FileRisk | undefined;
  readonly patchReview: PatchReviewBundle | undefined;
  readonly selectedPatchIndex: number;
  readonly build: BuildReport | undefined;
  readonly diagnosis: BuildDiagnosis | undefined;
  readonly appliedFix: AppliedFix | undefined;
  readonly baseline: PerformanceBaseline | undefined;
  readonly tuning: TuningComparison | undefined;
  readonly tuningApplication: TuningApplication | undefined;
  readonly profiles: readonly ScenarioProfile[] | undefined;
  readonly selectedProfileId: string | undefined;
  readonly profileResult: ScenarioProfileResult | undefined;
  readonly summary: SessionSummary | undefined;
  readonly exportedReport: ExportedReport | undefined;
}

/**
 * Phase and act form a discriminated union, while completed-act data remains cached for the
 * persistent inspector and summary. Optional cached fields therefore do not imply phase validity.
 */
export type MigrationFlowState = MigrationFlowPosition & MigrationFlowData;

export type ConfigurationValues = Readonly<Record<string, string | number>>;

export interface MigrationFlowActions {
  start(): Promise<void>;
  setIntentDraft(prompt: string, sourcePath?: string): void;
  submitIntent(): Promise<void>;
  updatePlan(steps: readonly EditablePlanStep[]): Promise<void>;
  executePlan(): Promise<void>;
  submitConfiguration(values: ConfigurationValues, skip?: boolean): Promise<void>;
  selectRiskFile(path: string): void;
  openPatchReview(): Promise<void>;
  selectPatch(index: number): void;
  reviewPatch(patchId: string, decision: Exclude<PatchDecision, "pending">): Promise<void>;
  runInitialBuild(): Promise<void>;
  diagnoseBuild(): Promise<void>;
  applyFixAndRetryBuild(): Promise<void>;
  collectBaseline(): Promise<void>;
  compareTuningPlans(): Promise<void>;
  applyTuningPlan(planId: string): Promise<void>;
  openProfiles(): Promise<void>;
  selectProfile(profileId: string): void;
  runSelectedProfile(): Promise<void>;
  finishSession(): Promise<void>;
  exportSummary(format: "markdown" | "json", destinationPath: string): Promise<void>;
  retry(): Promise<void>;
  cancelCurrent(): void;
  clearError(): void;
}

export const INITIAL_MIGRATION_FLOW_STATE: MigrationFlowState = {
  phase: "landing",
  act: 1,
  asyncStatus: "idle",
  pendingOperation: undefined,
  error: undefined,
  intent: {
    prompt: "把 ./nginx 迁移到鲲鹏 ARM64 并完成性能验证",
    sourcePath: "./nginx",
  },
  workspace: undefined,
  plan: undefined,
  configuration: undefined,
  configurationResolution: undefined,
  report: undefined,
  selectedRiskFile: undefined,
  patchReview: undefined,
  selectedPatchIndex: 0,
  build: undefined,
  diagnosis: undefined,
  appliedFix: undefined,
  baseline: undefined,
  tuning: undefined,
  tuningApplication: undefined,
  profiles: undefined,
  selectedProfileId: undefined,
  profileResult: undefined,
  summary: undefined,
  exportedReport: undefined,
};
