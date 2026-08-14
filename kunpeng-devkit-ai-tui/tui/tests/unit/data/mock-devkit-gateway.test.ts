import { describe, expect, it } from "vitest";
import {
  createMockDevKitGatewayFromEnvironment,
  type DelayScheduler,
  MockDevKitGateway,
  parseMockScenario,
  type ScheduledDelay,
} from "../../../src/data/adapters/mock";
import type { Result } from "../../../src/shared";

const signal = (): AbortSignal => new AbortController().signal;

class ManualDelayScheduler implements DelayScheduler {
  private readonly callbacks = new Set<() => void>();

  get pendingCount(): number {
    return this.callbacks.size;
  }

  schedule(_delayMs: number, callback: () => void): ScheduledDelay {
    this.callbacks.add(callback);
    return { cancel: () => this.callbacks.delete(callback) };
  }

  runAll(): void {
    const callbacks = [...this.callbacks];
    this.callbacks.clear();
    for (const callback of callbacks) callback();
  }
}

class ThrowingDelayScheduler implements DelayScheduler {
  schedule(_delayMs: number, _callback: () => void): ScheduledDelay {
    throw new Error("scheduler failed");
  }
}

// biome-ignore lint/suspicious/noShadowRestrictedNames: test helper mirrors Result value extraction.
function valueOf<T>(result: Result<T>): T {
  if (!result.ok) throw new Error(`${result.error.code}: ${result.error.message}`);
  return result.value;
}

describe("MockDevKitGateway", () => {
  it("converts scheduler failures into typed AppError results", async () => {
    const gateway = new MockDevKitGateway({
      latencyMs: 1,
      scheduler: new ThrowingDelayScheduler(),
    });
    await expect(gateway.loadWorkspaceBootstrap(signal())).resolves.toMatchObject({
      ok: false,
      error: {
        kind: "unexpected",
        code: "mock.unhandled-error",
        details: { operation: "workspace.bootstrap", cause: "scheduler failed" },
      },
    });
  });

  it("provides a deterministic ten-act happy path", async () => {
    const gateway = new MockDevKitGateway({ latencyMs: 0 });
    const workspace = valueOf(await gateway.loadWorkspaceBootstrap(signal()));
    expect(workspace.productName).toBe("Kunpeng DevKit AI");
    expect(workspace.binaryName).toBe("devkitai");

    const installed = valueOf(
      await gateway.installCapabilities({ capabilityIds: ["sql-migrator"] }, signal()),
    );
    expect(installed.installedCount).toBe(1);

    const plan = valueOf(
      await gateway.createMigrationPlan({ prompt: "迁移 nginx", sourcePath: "./nginx" }, signal()),
    );
    expect(plan.steps).toHaveLength(5);

    const editedPlan = valueOf(
      await gateway.updateMigrationPlan(
        {
          taskId: plan.taskId,
          expectedVersion: plan.version,
          steps: plan.steps.map((step) => ({ id: step.id, title: step.title, enabled: true })),
        },
        signal(),
      ),
    );
    expect(editedPlan.version).toBe(plan.version + 1);

    const requirement = valueOf(await gateway.loadConfigurationRequirement(plan.taskId, signal()));
    const resolution = valueOf(
      await gateway.resolveConfiguration(
        {
          taskId: plan.taskId,
          resumeToken: requirement.resumeToken,
          values: {
            toolchainPath: "/usr/bin/aarch64-linux-gnu-",
            outputDirectory: "./build-arm64",
            parallelism: 16,
          },
          skip: false,
        },
        signal(),
      ),
    );
    expect(resolution.status).toBe("resumed");

    const report = valueOf(
      await gateway.analyzeCompatibility(
        { taskId: plan.taskId, includeBuildScripts: true },
        signal(),
      ),
    );
    expect(report.compatibilityScore).toBe(82);
    expect(report.issues[0]?.evidence.length).toBeGreaterThan(0);

    const patches = valueOf(await gateway.loadPatchReview(plan.taskId, signal()));
    const reviewed = valueOf(
      await gateway.reviewPatch(
        { taskId: plan.taskId, patchId: patches.patches[0]?.id ?? "missing", decision: "accepted" },
        signal(),
      ),
    );
    expect(reviewed.acceptedCount).toBe(1);

    const firstBuild = valueOf(
      await gateway.runBuild({ taskId: plan.taskId, attempt: "initial" }, signal()),
    );
    expect(firstBuild.status).toBe("failed");
    const diagnosis = valueOf(await gateway.diagnoseBuild(plan.taskId, signal()));
    expect(diagnosis.confidence).toBe(0.91);
    expect(diagnosis.evidence).not.toHaveLength(0);
    const appliedFix = valueOf(
      await gateway.applyDiagnosisFix(
        { taskId: plan.taskId, fixId: diagnosis.proposedFixId },
        signal(),
      ),
    );
    expect(appliedFix.nextAction).toBe("rebuild");
    const rebuilt = valueOf(
      await gateway.runBuild({ taskId: plan.taskId, attempt: "after-fix" }, signal()),
    );
    expect(rebuilt.status).toBe("passed");

    const baseline = valueOf(await gateway.collectPerformanceBaseline(plan.taskId, signal()));
    expect(baseline.bottleneck).toBe("memory-bound");
    const comparison = valueOf(await gateway.compareTuningPlans(plan.taskId, signal()));
    const recommended = comparison.plans.find((candidate) => candidate.recommended);
    expect(recommended).toBeDefined();
    const tuning = valueOf(
      await gateway.applyTuningPlan(
        { taskId: plan.taskId, planId: recommended?.id ?? "missing" },
        signal(),
      ),
    );
    expect(tuning.after.qps).toBeGreaterThan(tuning.before.qps);

    const profiles = valueOf(await gateway.listScenarioProfiles(plan.taskId, signal()));
    const profile = valueOf(
      await gateway.runScenarioProfile(
        { taskId: plan.taskId, profileId: profiles[0]?.id ?? "missing" },
        signal(),
      ),
    );
    expect(profile.status).toBe("passed");

    const summary = valueOf(await gateway.loadSessionSummary(plan.taskId, signal()));
    expect(summary.buildStatus).toBe("passed");
    expect(summary.finalMetrics.qps).toBeGreaterThan(summary.baseline.qps);
  });

  it("isolates returned fixtures from consumer mutation", async () => {
    const gateway = new MockDevKitGateway({ latencyMs: 0 });
    const first = valueOf(await gateway.loadWorkspaceBootstrap(signal()));
    // Simulate an untyped JavaScript consumer violating readonly to verify the adapter boundary.
    (first.suggestions as string[]).push("consumer mutation");
    const second = valueOf(await gateway.loadWorkspaceBootstrap(signal()));
    expect(second.suggestions).not.toContain("consumer mutation");
  });

  it("validates user input, versions, tokens and identifiers", async () => {
    const gateway = new MockDevKitGateway({ latencyMs: 0 });
    const invalidPlan = await gateway.createMigrationPlan(
      { prompt: "  ", sourcePath: "./nginx" },
      signal(),
    );
    expect(invalidPlan).toMatchObject({ ok: false, error: { kind: "invalid-input" } });

    const conflict = await gateway.updateMigrationPlan(
      { taskId: "task-nginx-arm64", expectedVersion: 99, steps: [] },
      signal(),
    );
    expect(conflict).toMatchObject({ ok: false, error: { kind: "conflict" } });

    const missingTask = await gateway.loadSessionSummary("missing", signal());
    expect(missingTask).toMatchObject({ ok: false, error: { kind: "not-found" } });

    const invalidToken = await gateway.resolveConfiguration(
      { taskId: "task-nginx-arm64", resumeToken: "expired", values: {}, skip: true },
      signal(),
    );
    expect(invalidToken).toMatchObject({ ok: false, error: { kind: "conflict" } });
  });

  it("supports empty and extreme render-testing scenarios", async () => {
    const empty = new MockDevKitGateway({ scenario: "empty", latencyMs: 0 });
    const emptyWorkspace = valueOf(await empty.loadWorkspaceBootstrap(signal()));
    const emptyReport = valueOf(
      await empty.analyzeCompatibility(
        { taskId: "task-nginx-arm64", includeBuildScripts: true },
        signal(),
      ),
    );
    expect(emptyWorkspace.recentTasks).toEqual([]);
    expect(emptyReport.files).toEqual([]);

    const extreme = new MockDevKitGateway({ scenario: "extreme", latencyMs: 0 });
    const extremeReport = valueOf(
      await extreme.analyzeCompatibility(
        { taskId: "task-nginx-arm64", includeBuildScripts: true },
        signal(),
      ),
    );
    expect(extremeReport.files).toHaveLength(256);
    expect(extremeReport.files[0]?.path).toContain("非常长的模块名称");
  });

  it("distinguishes forced errors from offline failures", async () => {
    const forced = await new MockDevKitGateway({
      scenario: "error",
      latencyMs: 0,
    }).loadWorkspaceBootstrap(signal());
    expect(forced).toMatchObject({
      ok: false,
      error: { code: "mock.forced-error", retryable: true },
    });

    const offline = await new MockDevKitGateway({
      scenario: "offline",
      latencyMs: 0,
    }).loadWorkspaceBootstrap(signal());
    expect(offline).toMatchObject({ ok: false, error: { kind: "offline", retryable: true } });
  });

  it("honors AbortSignal before and during an operation", async () => {
    const before = new AbortController();
    before.abort();
    const cancelledBefore = await new MockDevKitGateway({ latencyMs: 0 }).loadWorkspaceBootstrap(
      before.signal,
    );
    expect(cancelledBefore).toMatchObject({ ok: false, error: { kind: "cancelled" } });

    const scheduler = new ManualDelayScheduler();
    const during = new AbortController();
    const request = new MockDevKitGateway({
      scenario: "slow",
      latencyMs: 100,
      scheduler,
    }).loadWorkspaceBootstrap(during.signal);
    expect(scheduler.pendingCount).toBe(1);
    during.abort();
    expect(scheduler.pendingCount).toBe(0);
    await expect(request).resolves.toMatchObject({
      ok: false,
      error: { kind: "cancelled" },
    });
  });

  it("uses an injectable scheduler for deterministic mock latency", async () => {
    const scheduler = new ManualDelayScheduler();
    const request = new MockDevKitGateway({ latencyMs: 250, scheduler }).loadWorkspaceBootstrap(
      signal(),
    );
    expect(scheduler.pendingCount).toBe(1);

    scheduler.runAll();

    await expect(request).resolves.toMatchObject({ ok: true });
    expect(scheduler.pendingCount).toBe(0);
  });

  it("parses environment scenarios safely", () => {
    expect(parseMockScenario("extreme")).toBe("extreme");
    expect(parseMockScenario("unknown")).toBe("happy");
    expect(
      createMockDevKitGatewayFromEnvironment({ DEVKITAI_MOCK_SCENARIO: "offline" }).scenario,
    ).toBe("offline");
  });
});
