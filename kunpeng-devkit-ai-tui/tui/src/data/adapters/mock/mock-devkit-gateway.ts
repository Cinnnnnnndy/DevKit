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
} from "../../../domain";
import {
  type AppError,
  cancelledError,
  createAppError,
  err,
  ok,
  type Result,
} from "../../../shared";
import { createDemoFixtures, type DemoFixtureSet, type MockScenario } from "../../fixtures";
import type { DevKitGateway } from "../../ports";

const DEFAULT_LATENCY_MS: Readonly<Record<MockScenario, number>> = {
  happy: 24,
  empty: 12,
  error: 16,
  slow: 800,
  offline: 0,
  extreme: 32,
};

export interface MockDevKitGatewayOptions {
  readonly scenario?: MockScenario;
  readonly latencyMs?: number;
  readonly scheduler?: DelayScheduler;
}

export interface ScheduledDelay {
  cancel(): void;
}

/** Injectable timing boundary so mock latency stays deterministic in tests. */
export interface DelayScheduler {
  schedule(delayMs: number, callback: () => void): ScheduledDelay;
}

const REAL_DELAY_SCHEDULER: DelayScheduler = {
  schedule(delayMs, callback) {
    const timer = setTimeout(callback, delayMs);
    return { cancel: () => clearTimeout(timer) };
  },
};

export function parseMockScenario(value: string | undefined): MockScenario {
  switch (value) {
    case "empty":
    case "error":
    case "slow":
    case "offline":
    case "extreme":
      return value;
    default:
      return "happy";
  }
}

export function createMockDevKitGatewayFromEnvironment(
  environment: Readonly<Record<string, string | undefined>> = process.env,
): MockDevKitGateway {
  return new MockDevKitGateway({
    scenario: parseMockScenario(environment["DEVKITAI_MOCK_SCENARIO"]),
  });
}

export class MockDevKitGateway implements DevKitGateway {
  readonly scenario: MockScenario;
  readonly latencyMs: number;

  private fixtures: DemoFixtureSet;
  private readonly scheduler: DelayScheduler;

  constructor(options: MockDevKitGatewayOptions = {}) {
    this.scenario = options.scenario ?? "happy";
    this.latencyMs = Math.max(0, options.latencyMs ?? DEFAULT_LATENCY_MS[this.scenario]);
    this.scheduler = options.scheduler ?? REAL_DELAY_SCHEDULER;
    this.fixtures = createDemoFixtures(this.scenario);
  }

  loadWorkspaceBootstrap(signal: AbortSignal): Promise<Result<WorkspaceBootstrap>> {
    return this.execute("workspace.bootstrap", signal, () =>
      ok(this.clone(this.fixtures.workspace)),
    );
  }

  installCapabilities(
    request: InstallCapabilitiesRequest,
    signal: AbortSignal,
  ): Promise<Result<InstallCapabilitiesResult>> {
    return this.execute("capability.install", signal, () => {
      const requested = new Set(request.capabilityIds);
      const capabilities = this.fixtures.workspace.capabilities.map((capability) =>
        requested.has(capability.id) && capability.status !== "blocked"
          ? { ...capability, status: "ready" as const }
          : capability,
      );
      const installedCount = capabilities.filter(
        (capability, index) =>
          capability.status === "ready" &&
          this.fixtures.workspace.capabilities[index]?.status !== "ready",
      ).length;
      this.fixtures = {
        ...this.fixtures,
        workspace: { ...this.fixtures.workspace, capabilities },
      };
      return ok({ capabilities: this.clone(capabilities), installedCount });
    });
  }

  createMigrationPlan(
    request: CreateMigrationPlanRequest,
    signal: AbortSignal,
  ): Promise<Result<MigrationPlan>> {
    return this.execute("migration.plan.create", signal, () => {
      if (request.prompt.trim().length === 0 || request.sourcePath.trim().length === 0) {
        return err(
          createAppError(
            "invalid-input",
            "migration.plan.invalid-input",
            "迁移目标和源码路径不能为空",
            false,
          ),
        );
      }
      const plan: MigrationPlan = {
        ...this.fixtures.plan,
        goal: request.prompt.trim(),
        sourcePath: request.sourcePath.trim(),
        sourceArchitecture: request.sourceArchitecture ?? "x86_64",
        targetArchitecture: request.targetArchitecture ?? "aarch64",
      };
      this.fixtures = { ...this.fixtures, plan };
      return ok(this.clone(plan));
    });
  }

  updateMigrationPlan(
    request: UpdateMigrationPlanRequest,
    signal: AbortSignal,
  ): Promise<Result<MigrationPlan>> {
    return this.execute("migration.plan.update", signal, () => {
      const taskError = this.validateTask(request.taskId);
      if (taskError !== undefined) return err(taskError);
      if (request.expectedVersion !== this.fixtures.plan.version) {
        return err(
          createAppError(
            "conflict",
            "migration.plan.version-conflict",
            "计划已更新，请重新载入后再修改",
            true,
          ),
        );
      }
      const existingSteps = new Map(this.fixtures.plan.steps.map((step) => [step.id, step]));
      const steps = request.steps
        .filter((step) => step.enabled)
        .map((editable) => {
          const existing = existingSteps.get(editable.id);
          return existing === undefined
            ? {
                id: editable.id,
                title: editable.title,
                description: editable.title,
                status: "pending" as const,
              }
            : { ...existing, title: editable.title };
        });
      const plan: MigrationPlan = {
        ...this.fixtures.plan,
        version: this.fixtures.plan.version + 1,
        steps,
      };
      this.fixtures = { ...this.fixtures, plan };
      return ok(this.clone(plan));
    });
  }

  loadConfigurationRequirement(
    taskId: TaskId,
    signal: AbortSignal,
  ): Promise<Result<ConfigurationRequirement>> {
    return this.taskFixture(
      "migration.configuration.load",
      taskId,
      signal,
      this.fixtures.configuration,
    );
  }

  resolveConfiguration(
    request: ResolveConfigurationRequest,
    signal: AbortSignal,
  ): Promise<Result<ConfigurationResolution>> {
    return this.execute("migration.configuration.resolve", signal, () => {
      const taskError = this.validateTask(request.taskId);
      if (taskError !== undefined) return err(taskError);
      if (request.resumeToken !== this.fixtures.configuration.resumeToken) {
        return err(
          createAppError(
            "conflict",
            "migration.configuration.resume-token-invalid",
            "任务恢复令牌已失效",
            false,
          ),
        );
      }
      if (!request.skip) {
        const missingField = this.fixtures.configuration.fields.find(
          (field) => field.required && request.values[field.key] === undefined,
        );
        if (missingField !== undefined) {
          return err(
            createAppError(
              "invalid-input",
              "migration.configuration.required-field",
              `缺少必填配置：${missingField.label}`,
              false,
              { field: missingField.key },
            ),
          );
        }
      }
      return ok({
        taskId: request.taskId,
        resumedStepId: this.fixtures.configuration.pausedStepId,
        status: request.skip ? "skipped" : "resumed",
      });
    });
  }

  analyzeCompatibility(
    request: CompatibilityAnalysisRequest,
    signal: AbortSignal,
  ): Promise<Result<MigrationReport>> {
    return this.taskFixture(
      "migration.compatibility.analyze",
      request.taskId,
      signal,
      this.fixtures.migrationReport,
    );
  }

  loadPatchReview(taskId: TaskId, signal: AbortSignal): Promise<Result<PatchReviewBundle>> {
    return this.taskFixture("migration.patch.load", taskId, signal, this.fixtures.patchReview);
  }

  reviewPatch(
    request: ReviewPatchRequest,
    signal: AbortSignal,
  ): Promise<Result<PatchReviewBundle>> {
    return this.execute("migration.patch.review", signal, () => {
      const taskError = this.validateTask(request.taskId);
      if (taskError !== undefined) return err(taskError);
      if (!this.fixtures.patchReview.patches.some((patch) => patch.id === request.patchId)) {
        return err(
          createAppError("not-found", "migration.patch.not-found", "未找到迁移补丁", false),
        );
      }
      const patches = this.fixtures.patchReview.patches.map((patch) =>
        patch.id === request.patchId ? { ...patch, decision: request.decision } : patch,
      );
      const patchReview: PatchReviewBundle = {
        taskId: request.taskId,
        patches,
        acceptedCount: patches.filter((patch) => patch.decision === "accepted").length,
        rejectedCount: patches.filter((patch) => patch.decision === "rejected").length,
        pendingCount: patches.filter((patch) => patch.decision === "pending").length,
      };
      this.fixtures = { ...this.fixtures, patchReview };
      return ok(this.clone(patchReview));
    });
  }

  runBuild(request: BuildRequest, signal: AbortSignal): Promise<Result<BuildReport>> {
    return this.taskFixture(
      "build.run",
      request.taskId,
      signal,
      request.attempt === "initial" ? this.fixtures.failedBuild : this.fixtures.passedBuild,
    );
  }

  diagnoseBuild(taskId: TaskId, signal: AbortSignal): Promise<Result<BuildDiagnosis>> {
    return this.taskFixture("build.diagnose", taskId, signal, this.fixtures.diagnosis);
  }

  applyDiagnosisFix(
    request: ApplyDiagnosisFixRequest,
    signal: AbortSignal,
  ): Promise<Result<AppliedFix>> {
    return this.execute("build.fix.apply", signal, () => {
      const taskError = this.validateTask(request.taskId);
      if (taskError !== undefined) return err(taskError);
      if (request.fixId !== this.fixtures.diagnosis.proposedFixId) {
        return err(createAppError("not-found", "build.fix.not-found", "未找到诊断修复方案", false));
      }
      return ok({
        taskId: request.taskId,
        fixId: request.fixId,
        changedFiles: ["src/os/unix/ngx_alloc.c"],
        nextAction: "rebuild",
      });
    });
  }

  collectPerformanceBaseline(
    taskId: TaskId,
    signal: AbortSignal,
  ): Promise<Result<PerformanceBaseline>> {
    return this.taskFixture("performance.baseline", taskId, signal, this.fixtures.performance);
  }

  compareTuningPlans(taskId: TaskId, signal: AbortSignal): Promise<Result<TuningComparison>> {
    return this.taskFixture("performance.tuning.compare", taskId, signal, this.fixtures.tuning);
  }

  applyTuningPlan(
    request: ApplyTuningPlanRequest,
    signal: AbortSignal,
  ): Promise<Result<TuningApplication>> {
    return this.execute("performance.tuning.apply", signal, () => {
      const taskError = this.validateTask(request.taskId);
      if (taskError !== undefined) return err(taskError);
      const plan = this.fixtures.tuning.plans.find((candidate) => candidate.id === request.planId);
      if (plan === undefined) {
        return err(
          createAppError("not-found", "performance.plan.not-found", "未找到调优方案", false),
        );
      }
      return ok({
        taskId: request.taskId,
        planId: plan.id,
        before: this.clone(this.fixtures.tuning.baseline),
        after: this.clone(plan.metrics),
        changedFiles: ["conf/nginx.conf", "scripts/set-numa-affinity.sh"],
      });
    });
  }

  listScenarioProfiles(
    taskId: TaskId,
    signal: AbortSignal,
  ): Promise<Result<readonly ScenarioProfile[]>> {
    return this.taskFixture("performance.profile.list", taskId, signal, this.fixtures.profiles);
  }

  runScenarioProfile(
    request: RunScenarioProfileRequest,
    signal: AbortSignal,
  ): Promise<Result<ScenarioProfileResult>> {
    return this.execute("performance.profile.run", signal, () => {
      const taskError = this.validateTask(request.taskId);
      if (taskError !== undefined) return err(taskError);
      if (!this.fixtures.profiles.some((profile) => profile.id === request.profileId)) {
        return err(
          createAppError("not-found", "performance.profile.not-found", "未找到场景 Profile", false),
        );
      }
      return ok(this.clone({ ...this.fixtures.profileResult, profileId: request.profileId }));
    });
  }

  loadSessionSummary(taskId: TaskId, signal: AbortSignal): Promise<Result<SessionSummary>> {
    return this.taskFixture("session.summary", taskId, signal, this.fixtures.summary);
  }

  private taskFixture<T>(
    operation: string,
    taskId: TaskId,
    signal: AbortSignal,
    fixture: T,
  ): Promise<Result<T>> {
    return this.execute(operation, signal, () => {
      const taskError = this.validateTask(taskId);
      return taskError === undefined ? ok(this.clone(fixture)) : err(taskError);
    });
  }

  private async execute<T>(
    operation: string,
    signal: AbortSignal,
    producer: () => Result<T>,
  ): Promise<Result<T>> {
    if (signal.aborted) return err(cancelledError());
    let waited: Result<void>;
    try {
      waited = await this.wait(signal);
    } catch (cause) {
      return err(this.unexpectedError(operation, cause));
    }
    if (!waited.ok) return waited;
    if (this.scenario === "offline") {
      return err(
        createAppError("offline", "mock.offline", "Mock 数据源处于离线场景", true, {
          operation,
        }),
      );
    }
    if (this.scenario === "error") {
      return err(
        createAppError("unexpected", "mock.forced-error", "Mock 场景强制返回失败", true, {
          operation,
        }),
      );
    }
    try {
      return producer();
    } catch (cause) {
      return err(this.unexpectedError(operation, cause));
    }
  }

  private wait(signal: AbortSignal): Promise<Result<void>> {
    if (signal.aborted) return Promise.resolve(err(cancelledError()));
    if (this.latencyMs === 0) return Promise.resolve(ok(undefined));
    return new Promise((resolve) => {
      let settled = false;
      let scheduled: ScheduledDelay | undefined;
      const settle = (result: Result<void>): void => {
        if (settled) return;
        settled = true;
        signal.removeEventListener("abort", onAbort);
        resolve(result);
      };
      const onAbort = (): void => {
        scheduled?.cancel();
        settle(err(cancelledError()));
      };
      signal.addEventListener("abort", onAbort, { once: true });
      // A scheduler may settle synchronously, while abort can race between listener setup and scheduling.
      if (signal.aborted) return onAbort();
      scheduled = this.scheduler.schedule(this.latencyMs, () => settle(ok(undefined)));
      if (settled) scheduled.cancel();
    });
  }

  private validateTask(taskId: TaskId): AppError | undefined {
    return taskId === this.fixtures.plan.taskId
      ? undefined
      : createAppError("not-found", "task.not-found", `未找到任务：${taskId}`, false, { taskId });
  }

  private unexpectedError(operation: string, cause: unknown): AppError {
    return createAppError("unexpected", "mock.unhandled-error", "Mock 数据适配器执行失败", true, {
      operation,
      cause: cause instanceof Error ? cause.message : String(cause),
    });
  }

  private clone<T>(value: T): T {
    // Clone at the port boundary so consumer mutation can never corrupt reusable fixture state.
    return structuredClone(value);
  }
}
