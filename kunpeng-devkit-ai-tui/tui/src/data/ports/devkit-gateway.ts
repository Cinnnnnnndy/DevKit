import type {
  AppliedFix,
  ApplyDiagnosisFixRequest,
  ApplyTuningPlanRequest,
  BuildDiagnosis,
  BuildReport,
  BuildRequest,
  CompatibilityAnalysisRequest,
  ConfigurationRequirement,
  ConfigurationResolution,
  CreateMigrationPlanRequest,
  InstallCapabilitiesRequest,
  InstallCapabilitiesResult,
  MigrationPlan,
  MigrationReport,
  PatchReviewBundle,
  PerformanceBaseline,
  ResolveConfigurationRequest,
  ReviewPatchRequest,
  RunScenarioProfileRequest,
  ScenarioProfile,
  ScenarioProfileResult,
  SessionSummary,
  TaskId,
  TuningApplication,
  TuningComparison,
  UpdateMigrationPlanRequest,
  WorkspaceBootstrap,
} from "../../domain";
import type { Result } from "../../shared";

export interface DevKitGateway {
  loadWorkspaceBootstrap(signal: AbortSignal): Promise<Result<WorkspaceBootstrap>>;
  installCapabilities(
    request: InstallCapabilitiesRequest,
    signal: AbortSignal,
  ): Promise<Result<InstallCapabilitiesResult>>;
  createMigrationPlan(
    request: CreateMigrationPlanRequest,
    signal: AbortSignal,
  ): Promise<Result<MigrationPlan>>;
  updateMigrationPlan(
    request: UpdateMigrationPlanRequest,
    signal: AbortSignal,
  ): Promise<Result<MigrationPlan>>;
  loadConfigurationRequirement(
    taskId: TaskId,
    signal: AbortSignal,
  ): Promise<Result<ConfigurationRequirement>>;
  resolveConfiguration(
    request: ResolveConfigurationRequest,
    signal: AbortSignal,
  ): Promise<Result<ConfigurationResolution>>;
  analyzeCompatibility(
    request: CompatibilityAnalysisRequest,
    signal: AbortSignal,
  ): Promise<Result<MigrationReport>>;
  loadPatchReview(taskId: TaskId, signal: AbortSignal): Promise<Result<PatchReviewBundle>>;
  reviewPatch(request: ReviewPatchRequest, signal: AbortSignal): Promise<Result<PatchReviewBundle>>;
  runBuild(request: BuildRequest, signal: AbortSignal): Promise<Result<BuildReport>>;
  diagnoseBuild(taskId: TaskId, signal: AbortSignal): Promise<Result<BuildDiagnosis>>;
  applyDiagnosisFix(
    request: ApplyDiagnosisFixRequest,
    signal: AbortSignal,
  ): Promise<Result<AppliedFix>>;
  collectPerformanceBaseline(
    taskId: TaskId,
    signal: AbortSignal,
  ): Promise<Result<PerformanceBaseline>>;
  compareTuningPlans(taskId: TaskId, signal: AbortSignal): Promise<Result<TuningComparison>>;
  applyTuningPlan(
    request: ApplyTuningPlanRequest,
    signal: AbortSignal,
  ): Promise<Result<TuningApplication>>;
  listScenarioProfiles(
    taskId: TaskId,
    signal: AbortSignal,
  ): Promise<Result<readonly ScenarioProfile[]>>;
  runScenarioProfile(
    request: RunScenarioProfileRequest,
    signal: AbortSignal,
  ): Promise<Result<ScenarioProfileResult>>;
  loadSessionSummary(taskId: TaskId, signal: AbortSignal): Promise<Result<SessionSummary>>;
}
