import { describe, expect, it } from "vitest";
import {
  type DelayScheduler,
  MemoryReportExporter,
  MockDevKitGateway,
  type ScheduledDelay,
} from "../../../src/data/adapters/mock";
import type { DevKitGateway } from "../../../src/data/ports";
import { MigrationFlowController } from "../../../src/features/migration-flow";
import { createAppError, err } from "../../../src/shared";

class ManualDelayScheduler implements DelayScheduler {
  private readonly callbacks = new Set<() => void>();

  schedule(_delayMs: number, callback: () => void): ScheduledDelay {
    this.callbacks.add(callback);
    return { cancel: () => this.callbacks.delete(callback) };
  }
}

class FlakyBootstrapGateway extends MockDevKitGateway {
  attempts = 0;

  override loadWorkspaceBootstrap(
    signal: AbortSignal,
  ): ReturnType<DevKitGateway["loadWorkspaceBootstrap"]> {
    this.attempts += 1;
    if (this.attempts === 1) {
      return Promise.resolve(
        err(createAppError("timeout", "test.transient", "temporary timeout", true)),
      );
    }
    return super.loadWorkspaceBootstrap(signal);
  }
}

class FailingPatchReviewGateway extends MockDevKitGateway {
  attempts = 0;

  override reviewPatch(
    _request: Parameters<DevKitGateway["reviewPatch"]>[0],
    _signal: Parameters<DevKitGateway["reviewPatch"]>[1],
  ): ReturnType<DevKitGateway["reviewPatch"]> {
    this.attempts += 1;
    return Promise.resolve(
      err(createAppError("timeout", "test.patch-timeout", "temporary timeout", true)),
    );
  }
}

function createController(gateway: DevKitGateway = new MockDevKitGateway({ latencyMs: 0 })) {
  const reportExporter = new MemoryReportExporter();
  return {
    gateway,
    reportExporter,
    controller: new MigrationFlowController({ gateway, reportExporter }),
  };
}

async function enterPlan(controller: MigrationFlowController): Promise<void> {
  await controller.start();
  controller.setIntentDraft("把 ./nginx 迁移到鲲鹏 ARM64", "./nginx");
  await controller.submitIntent();
}

describe("MigrationFlowController", () => {
  it("completes all ten acts through the shared task state machine", async () => {
    const { controller, reportExporter } = createController();
    const visitedActs = new Set<number>();
    const capture = (): void => {
      visitedActs.add(controller.getSnapshot().act);
    };

    await controller.start();
    capture();
    expect(controller.getSnapshot()).toMatchObject({ phase: "landing", asyncStatus: "ready" });

    controller.setIntentDraft("把 ./nginx 迁移到鲲鹏 ARM64", "./nginx");
    await controller.submitIntent();
    capture();
    expect(controller.getSnapshot()).toMatchObject({ phase: "plan", act: 2 });

    const initialPlan = controller.getSnapshot().plan;
    expect(initialPlan).toBeDefined();
    await controller.updatePlan(
      initialPlan?.steps.map((step) => ({ id: step.id, title: step.title, enabled: true })) ?? [],
    );
    expect(controller.getSnapshot().plan?.version).toBe(2);

    await controller.executePlan();
    capture();
    expect(controller.getSnapshot()).toMatchObject({ phase: "config", act: 3 });

    const configuration = controller.getSnapshot().configuration;
    expect(configuration).toBeDefined();
    const values = Object.fromEntries(
      configuration?.fields.map((field) => [field.key, field.defaultValue ?? ""]) ?? [],
    );
    await controller.submitConfiguration(values);
    capture();
    expect(controller.getSnapshot()).toMatchObject({
      phase: "report",
      act: 4,
      report: { compatibilityScore: 82 },
    });

    await controller.openPatchReview();
    capture();
    expect(controller.getSnapshot()).toMatchObject({ phase: "patch-review", act: 5 });
    const patches = controller.getSnapshot().patchReview?.patches ?? [];
    for (const patch of patches) await controller.reviewPatch(patch.id, "accepted");
    expect(controller.getSnapshot().patchReview?.pendingCount).toBe(0);
    expect(controller.getSnapshot().asyncStatus).toBe("ready");

    await controller.runInitialBuild();
    capture();
    expect(controller.getSnapshot()).toMatchObject({
      phase: "build-failed",
      act: 6,
      build: { status: "failed" },
    });

    await controller.diagnoseBuild();
    expect(controller.getSnapshot()).toMatchObject({
      phase: "diagnosis",
      diagnosis: { confidence: 0.91 },
    });
    await controller.applyFixAndRetryBuild();
    expect(controller.getSnapshot()).toMatchObject({
      phase: "build-passed",
      build: { status: "passed" },
    });

    await controller.collectBaseline();
    capture();
    expect(controller.getSnapshot()).toMatchObject({
      phase: "baseline",
      act: 7,
      baseline: { bottleneck: "memory-bound" },
    });

    await controller.compareTuningPlans();
    capture();
    expect(controller.getSnapshot()).toMatchObject({ phase: "tuning", act: 8 });
    const recommended = controller.getSnapshot().tuning?.plans.find((plan) => plan.recommended);
    expect(recommended).toBeDefined();
    await controller.applyTuningPlan(recommended?.id ?? "missing");
    expect(controller.getSnapshot().tuningApplication?.after.qps).toBeGreaterThan(
      controller.getSnapshot().tuningApplication?.before.qps ?? Number.POSITIVE_INFINITY,
    );

    await controller.openProfiles();
    capture();
    expect(controller.getSnapshot()).toMatchObject({ phase: "profile", act: 9 });
    await controller.runSelectedProfile();
    expect(controller.getSnapshot().profileResult?.status).toBe("passed");

    await controller.finishSession();
    capture();
    expect(controller.getSnapshot()).toMatchObject({
      phase: "summary",
      act: 10,
      summary: { buildStatus: "passed" },
    });
    await controller.exportSummary("markdown", "reports/nginx-migration.md");
    expect(controller.getSnapshot().exportedReport?.destinationPath).toBe(
      "reports/nginx-migration.md",
    );
    expect(controller.getSnapshot().asyncStatus).toBe("ready");
    expect(reportExporter.read("reports/nginx-migration.md")).toContain("Build: PASSED");

    expect([...visitedActs]).toEqual([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]);
  });

  it("keeps the current phase on adapter failure and retries the exact action", async () => {
    const flakyGateway = new FlakyBootstrapGateway({ latencyMs: 0 });
    const { controller } = createController(flakyGateway);

    await controller.start();
    expect(controller.getSnapshot()).toMatchObject({
      phase: "landing",
      asyncStatus: "error",
      error: { code: "test.transient", retryable: true },
    });

    await controller.retry();
    expect(controller.getSnapshot()).toMatchObject({
      phase: "landing",
      asyncStatus: "ready",
      error: undefined,
    });
    expect(flakyGateway.attempts).toBe(2);

    await controller.retry();
    expect(flakyGateway.attempts).toBe(2);
  });

  it("cancels an in-flight request without discarding the current phase", async () => {
    const scheduler = new ManualDelayScheduler();
    const { controller } = createController(
      new MockDevKitGateway({ scenario: "slow", latencyMs: 80, scheduler }),
    );
    const request = controller.start();
    expect(controller.getSnapshot()).toMatchObject({
      phase: "landing",
      asyncStatus: "loading",
      pendingOperation: "workspace.bootstrap",
    });
    controller.cancelCurrent();
    await request;

    expect(controller.getSnapshot()).toMatchObject({
      phase: "landing",
      asyncStatus: "cancelled",
      error: { kind: "cancelled" },
    });
  });

  it("surfaces a plan version conflict and can recover by regenerating the plan", async () => {
    const { controller, gateway } = createController();
    await enterPlan(controller);
    const stalePlan = controller.getSnapshot().plan;
    expect(stalePlan).toBeDefined();

    const externalUpdate = await gateway.updateMigrationPlan(
      {
        taskId: stalePlan?.taskId ?? "missing",
        expectedVersion: stalePlan?.version ?? -1,
        steps:
          stalePlan?.steps.map((step) => ({ id: step.id, title: step.title, enabled: true })) ?? [],
      },
      new AbortController().signal,
    );
    expect(externalUpdate.ok).toBe(true);

    await controller.updatePlan(
      stalePlan?.steps.map((step) => ({ id: step.id, title: step.title, enabled: true })) ?? [],
    );
    expect(controller.getSnapshot()).toMatchObject({
      phase: "plan",
      asyncStatus: "error",
      error: { kind: "conflict", code: "migration.plan.version-conflict" },
    });

    await controller.submitIntent();
    expect(controller.getSnapshot()).toMatchObject({
      phase: "plan",
      asyncStatus: "ready",
      plan: { version: 2 },
    });
  });

  it("blocks build verification while patch decisions remain pending", async () => {
    const { controller } = createController();
    await enterPlan(controller);
    await controller.executePlan();
    const configuration = controller.getSnapshot().configuration;
    await controller.submitConfiguration(
      Object.fromEntries(
        configuration?.fields.map((field) => [field.key, field.defaultValue ?? ""]) ?? [],
      ),
    );
    await controller.openPatchReview();
    await controller.runInitialBuild();

    expect(controller.getSnapshot()).toMatchObject({
      phase: "patch-review",
      asyncStatus: "error",
      error: { code: "migration.patch.pending", retryable: false },
    });
  });

  it("does not replay a stale high-risk retry after a local non-retryable failure", async () => {
    const gateway = new FailingPatchReviewGateway({ latencyMs: 0 });
    const { controller } = createController(gateway);
    await enterPlan(controller);
    await controller.executePlan();
    const configuration = controller.getSnapshot().configuration;
    await controller.submitConfiguration(
      Object.fromEntries(
        configuration?.fields.map((field) => [field.key, field.defaultValue ?? ""]) ?? [],
      ),
    );
    await controller.openPatchReview();
    const patchId = controller.getSnapshot().patchReview?.patches[0]?.id;
    expect(patchId).toBeDefined();

    await controller.reviewPatch(patchId ?? "missing", "accepted");
    expect(controller.getSnapshot().error).toMatchObject({
      code: "test.patch-timeout",
      retryable: true,
    });
    expect(gateway.attempts).toBe(1);

    await controller.runInitialBuild();
    expect(controller.getSnapshot().error).toMatchObject({
      code: "migration.patch.pending",
      retryable: false,
    });
    await controller.retry();

    expect(gateway.attempts).toBe(1);
    expect(controller.getSnapshot().error?.code).toBe("migration.patch.pending");
  });
});
