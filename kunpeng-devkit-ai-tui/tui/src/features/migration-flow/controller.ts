import type { DevKitGateway, ReportExporter } from "../../data/ports";
import type { EditablePlanStep, ExportedReport, PatchDecision, TaskId } from "../../domain";
import { type AppError, createAppError, err, ok, type Result } from "../../shared";
import {
  type ConfigurationValues,
  INITIAL_MIGRATION_FLOW_STATE,
  type MigrationFlowActions,
  type MigrationFlowState,
} from "./types";

type Listener = () => void;
type RetryAction = () => Promise<void>;

interface ControllerDependencies {
  readonly gateway: DevKitGateway;
  readonly reportExporter?: ReportExporter;
}

export class MigrationFlowController implements MigrationFlowActions {
  private state: MigrationFlowState = INITIAL_MIGRATION_FLOW_STATE;
  private readonly listeners = new Set<Listener>();
  private readonly gateway: DevKitGateway;
  private readonly reportExporter: ReportExporter | undefined;
  private activeRequest: AbortController | undefined;
  private operationSequence = 0;
  private retryAction: RetryAction | undefined;

  constructor({ gateway, reportExporter }: ControllerDependencies) {
    this.gateway = gateway;
    this.reportExporter = reportExporter;
  }

  getSnapshot = (): MigrationFlowState => this.state;

  subscribe = (listener: Listener): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  async start(): Promise<void> {
    await this.perform(
      "workspace.bootstrap",
      () => this.start(),
      (signal) => this.gateway.loadWorkspaceBootstrap(signal),
      (workspace) => ({
        ...this.state,
        phase: "landing",
        act: 1,
        asyncStatus:
          workspace.capabilities.length === 0 && workspace.recentTasks.length === 0
            ? "empty"
            : "ready",
        workspace,
      }),
    );
  }

  setIntentDraft(prompt: string, sourcePath = this.state.intent.sourcePath): void {
    this.patch({ intent: { prompt, sourcePath }, error: undefined });
  }

  async submitIntent(): Promise<void> {
    const intent = this.state.intent;
    await this.perform(
      "migration.plan.create",
      () => this.submitIntent(),
      (signal) =>
        this.gateway.createMigrationPlan(
          {
            prompt: intent.prompt,
            sourcePath: intent.sourcePath,
            sourceArchitecture: "x86_64",
            targetArchitecture: "aarch64",
          },
          signal,
        ),
      (plan) => ({
        ...this.state,
        phase: "plan",
        act: 2,
        asyncStatus: plan.steps.length === 0 ? "empty" : "ready",
        plan,
      }),
    );
  }

  async updatePlan(steps: readonly EditablePlanStep[]): Promise<void> {
    const plan = this.state.plan;
    if (plan === undefined) return this.failLocally("migration.plan.missing", "当前没有可编辑计划");
    await this.perform(
      "migration.plan.update",
      () => this.updatePlan(steps),
      (signal) =>
        this.gateway.updateMigrationPlan(
          { taskId: plan.taskId, expectedVersion: plan.version, steps },
          signal,
        ),
      (updatedPlan) => ({
        ...this.state,
        phase: "plan",
        act: 2,
        asyncStatus: updatedPlan.steps.length === 0 ? "empty" : "ready",
        plan: updatedPlan,
      }),
    );
  }

  async executePlan(): Promise<void> {
    const taskId = this.taskId();
    if (taskId === undefined) return;
    await this.perform(
      "migration.configuration.load",
      () => this.executePlan(),
      (signal) => this.gateway.loadConfigurationRequirement(taskId, signal),
      (configuration) => ({
        ...this.state,
        phase: "config",
        act: 3,
        asyncStatus: configuration.fields.length === 0 ? "empty" : "ready",
        configuration,
      }),
    );
  }

  async submitConfiguration(values: ConfigurationValues, skip = false): Promise<void> {
    const configuration = this.state.configuration;
    if (configuration === undefined) {
      return this.failLocally("migration.configuration.missing", "当前没有待补充配置");
    }
    await this.perform(
      "migration.configuration-and-analysis",
      () => this.submitConfiguration(values, skip),
      async (signal) => {
        const resolution = await this.gateway.resolveConfiguration(
          {
            taskId: configuration.taskId,
            resumeToken: configuration.resumeToken,
            values,
            skip,
          },
          signal,
        );
        if (!resolution.ok) return resolution;
        const report = await this.gateway.analyzeCompatibility(
          { taskId: configuration.taskId, includeBuildScripts: true },
          signal,
        );
        return report.ok ? ok({ resolution: resolution.value, report: report.value }) : report;
      },
      ({ resolution, report }) => ({
        ...this.state,
        phase: "report",
        act: 4,
        asyncStatus: report.files.length === 0 && report.issues.length === 0 ? "empty" : "ready",
        configurationResolution: resolution,
        report,
        selectedRiskFile: report.files[0],
      }),
    );
  }

  selectRiskFile(path: string): void {
    this.patch({
      selectedRiskFile: this.state.report?.files.find((file) => file.path === path),
    });
  }

  async openPatchReview(): Promise<void> {
    const taskId = this.taskId();
    if (taskId === undefined) return;
    await this.perform(
      "migration.patch.load",
      () => this.openPatchReview(),
      (signal) => this.gateway.loadPatchReview(taskId, signal),
      (patchReview) => ({
        ...this.state,
        phase: "patch-review",
        act: 5,
        asyncStatus: patchReview.patches.length === 0 ? "empty" : "ready",
        patchReview,
        selectedPatchIndex: 0,
      }),
    );
  }

  selectPatch(index: number): void {
    const count = this.state.patchReview?.patches.length ?? 0;
    this.patch({ selectedPatchIndex: Math.max(0, Math.min(Math.max(0, count - 1), index)) });
  }

  async reviewPatch(patchId: string, decision: Exclude<PatchDecision, "pending">): Promise<void> {
    const taskId = this.taskId();
    if (taskId === undefined) return;
    await this.perform(
      "migration.patch.review",
      () => this.reviewPatch(patchId, decision),
      (signal) => this.gateway.reviewPatch({ taskId, patchId, decision }, signal),
      (patchReview) => ({ ...this.state, phase: "patch-review", act: 5, patchReview }),
    );
  }

  async runInitialBuild(): Promise<void> {
    const taskId = this.taskId();
    if (taskId === undefined) return;
    if ((this.state.patchReview?.pendingCount ?? 0) > 0) {
      return this.failLocally(
        "migration.patch.pending",
        "仍有补丁未审查，完成接受或拒绝后才能构建",
      );
    }
    await this.perform(
      "build.initial",
      () => this.runInitialBuild(),
      (signal) => this.gateway.runBuild({ taskId, attempt: "initial" }, signal),
      (build) => ({
        ...this.state,
        phase: build.status === "failed" ? "build-failed" : "build-passed",
        act: 6,
        asyncStatus: "ready",
        build,
      }),
    );
  }

  async diagnoseBuild(): Promise<void> {
    const taskId = this.taskId();
    if (taskId === undefined) return;
    await this.perform(
      "build.diagnose",
      () => this.diagnoseBuild(),
      (signal) => this.gateway.diagnoseBuild(taskId, signal),
      (diagnosis) => ({
        ...this.state,
        phase: "diagnosis",
        act: 6,
        asyncStatus: diagnosis.evidence.length === 0 ? "empty" : "ready",
        diagnosis,
      }),
    );
  }

  async applyFixAndRetryBuild(): Promise<void> {
    const taskId = this.taskId();
    if (taskId === undefined) return;
    const diagnosis = this.state.diagnosis;
    if (diagnosis === undefined) {
      return this.failLocally("build.diagnosis.missing", "当前没有可应用的诊断修复");
    }
    await this.perform(
      "build.fix-and-retry",
      () => this.applyFixAndRetryBuild(),
      async (signal) => {
        const appliedFix = await this.gateway.applyDiagnosisFix(
          { taskId, fixId: diagnosis.proposedFixId },
          signal,
        );
        if (!appliedFix.ok) return appliedFix;
        const build = await this.gateway.runBuild({ taskId, attempt: "after-fix" }, signal);
        return build.ok ? ok({ appliedFix: appliedFix.value, build: build.value }) : build;
      },
      ({ appliedFix, build }) => ({
        ...this.state,
        phase: build.status === "passed" ? "build-passed" : "build-failed",
        act: 6,
        asyncStatus: "ready",
        appliedFix,
        build,
      }),
    );
  }

  async collectBaseline(): Promise<void> {
    const taskId = this.taskId();
    if (taskId === undefined) return;
    await this.perform(
      "performance.baseline",
      () => this.collectBaseline(),
      (signal) => this.gateway.collectPerformanceBaseline(taskId, signal),
      (baseline) => ({
        ...this.state,
        phase: "baseline",
        act: 7,
        asyncStatus: baseline.trace.length === 0 ? "empty" : "ready",
        baseline,
      }),
    );
  }

  async compareTuningPlans(): Promise<void> {
    const taskId = this.taskId();
    if (taskId === undefined) return;
    await this.perform(
      "performance.tuning.compare",
      () => this.compareTuningPlans(),
      (signal) => this.gateway.compareTuningPlans(taskId, signal),
      (tuning) => ({
        ...this.state,
        phase: "tuning",
        act: 8,
        asyncStatus: tuning.plans.length === 0 ? "empty" : "ready",
        tuning,
      }),
    );
  }

  async applyTuningPlan(planId: string): Promise<void> {
    const taskId = this.taskId();
    if (taskId === undefined) return;
    await this.perform(
      "performance.tuning.apply",
      () => this.applyTuningPlan(planId),
      (signal) => this.gateway.applyTuningPlan({ taskId, planId }, signal),
      (tuningApplication) => ({
        ...this.state,
        phase: "tuning",
        act: 8,
        tuningApplication,
      }),
    );
  }

  async openProfiles(): Promise<void> {
    const taskId = this.taskId();
    if (taskId === undefined) return;
    await this.perform(
      "performance.profile.list",
      () => this.openProfiles(),
      (signal) => this.gateway.listScenarioProfiles(taskId, signal),
      (profiles) => ({
        ...this.state,
        phase: "profile",
        act: 9,
        asyncStatus: profiles.length === 0 ? "empty" : "ready",
        profiles,
        selectedProfileId: profiles[0]?.id,
      }),
    );
  }

  selectProfile(profileId: string): void {
    if (this.state.profiles?.some((profile) => profile.id === profileId)) {
      this.patch({ selectedProfileId: profileId });
    }
  }

  async runSelectedProfile(): Promise<void> {
    const taskId = this.taskId();
    if (taskId === undefined) return;
    const profileId = this.state.selectedProfileId;
    if (profileId === undefined) {
      return this.failLocally("performance.profile.missing", "请选择场景 Profile");
    }
    await this.perform(
      "performance.profile.run",
      () => this.runSelectedProfile(),
      (signal) => this.gateway.runScenarioProfile({ taskId, profileId }, signal),
      (profileResult) => ({ ...this.state, phase: "profile", act: 9, profileResult }),
    );
  }

  async finishSession(): Promise<void> {
    const taskId = this.taskId();
    if (taskId === undefined) return;
    await this.perform(
      "session.summary",
      () => this.finishSession(),
      (signal) => this.gateway.loadSessionSummary(taskId, signal),
      (summary) => ({
        ...this.state,
        phase: "summary",
        act: 10,
        asyncStatus: "ready",
        summary,
      }),
    );
  }

  async exportSummary(format: "markdown" | "json", destinationPath: string): Promise<void> {
    const summary = this.state.summary;
    if (summary === undefined) {
      return this.failLocally("session.summary.missing", "当前没有可导出的会话摘要");
    }
    const exporter = this.reportExporter;
    if (exporter === undefined) {
      return this.failLocally("session.exporter.missing", "当前未配置报告导出器");
    }
    await this.perform<ExportedReport>(
      "session.export",
      () => this.exportSummary(format, destinationPath),
      (signal) => exporter.exportReport({ summary, format, destinationPath }, signal),
      (exportedReport) => ({ ...this.state, phase: "summary", act: 10, exportedReport }),
    );
  }

  async retry(): Promise<void> {
    const retryableState =
      this.state.asyncStatus === "cancelled" ||
      (this.state.asyncStatus === "error" && this.state.error?.retryable === true);
    if (!retryableState) return;
    const action = this.retryAction;
    if (action !== undefined) await action();
  }

  cancelCurrent(): void {
    if (this.activeRequest === undefined) return;
    this.activeRequest.abort();
  }

  clearError(): void {
    this.retryAction = undefined;
    this.patch({
      error: undefined,
      asyncStatus:
        this.state.phase === "landing" && this.state.workspace === undefined ? "idle" : "ready",
    });
  }

  private async perform<T>(
    operation: string,
    retryAction: RetryAction,
    request: (signal: AbortSignal) => Promise<Result<T>>,
    reduce: (value: T) => MigrationFlowState,
  ): Promise<void> {
    this.activeRequest?.abort();
    const abortController = new AbortController();
    const sequence = ++this.operationSequence;
    this.activeRequest = abortController;
    this.retryAction = retryAction;
    this.patch({ asyncStatus: "loading", pendingOperation: operation, error: undefined });

    let result: Result<T>;
    try {
      result = await request(abortController.signal);
    } catch (cause) {
      result = err(
        createAppError(
          "unexpected",
          "gateway.unhandled-error",
          "数据适配器返回了未处理异常",
          true,
          {
            operation,
            cause: cause instanceof Error ? cause.message : String(cause),
          },
        ),
      );
    }
    // An aborted adapter may still settle later; only the newest operation may update shared state.
    if (sequence !== this.operationSequence) return;
    this.activeRequest = undefined;

    if (!result.ok) {
      this.retryAction =
        result.error.kind === "cancelled" || result.error.retryable ? retryAction : undefined;
      this.patch({
        asyncStatus: result.error.kind === "cancelled" ? "cancelled" : "error",
        pendingOperation: undefined,
        error: result.error,
      });
      return;
    }

    const reduced = reduce(result.value);
    this.retryAction = undefined;
    this.state = {
      ...reduced,
      asyncStatus: reduced.asyncStatus === "loading" ? "ready" : reduced.asyncStatus,
      pendingOperation: undefined,
      error: undefined,
    };
    this.emit();
  }

  private taskId(): TaskId | undefined {
    const taskId = this.state.plan?.taskId;
    if (taskId === undefined) this.failLocally("task.missing", "当前没有迁移任务");
    return taskId;
  }

  private failLocally(code: string, message: string): void {
    const error: AppError = createAppError("invalid-input", code, message, false);
    this.retryAction = undefined;
    this.patch({ asyncStatus: "error", pendingOperation: undefined, error });
  }

  private patch(patch: Partial<Omit<MigrationFlowState, "phase" | "act">>): void {
    this.state = { ...this.state, ...patch };
    this.emit();
  }

  private emit(): void {
    for (const listener of this.listeners) listener();
  }
}
