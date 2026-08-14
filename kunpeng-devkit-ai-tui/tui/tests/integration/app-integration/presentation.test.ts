import { describe, expect, it } from "vitest";
import { presentationFromFlow } from "../../../src/app/index.js";
import { MemoryReportExporter, MockDevKitGateway } from "../../../src/data/adapters/mock/index.js";
import { MigrationFlowController } from "../../../src/features/migration-flow/index.js";

function configurationValues(controller: MigrationFlowController) {
  return Object.fromEntries(
    controller
      .getSnapshot()
      .configuration?.fields.map((field) => [field.key, field.defaultValue ?? ""]) ?? [],
  );
}

describe("App flow-to-chrome integration", () => {
  it("derives tabs, status, files, console and mode from real controller state", async () => {
    const controller = new MigrationFlowController({
      gateway: new MockDevKitGateway({ latencyMs: 0 }),
      reportExporter: new MemoryReportExporter(),
    });
    await controller.start();

    const landing = presentationFromFlow(controller.getSnapshot());
    expect(landing.tasks).toHaveLength(1);
    expect(landing.tasks[0]).toMatchObject({ label: "migrate nginx", status: "running" });
    expect(landing.consoleEvents[0]?.label).toBe("Local runtime ready");

    await controller.submitIntent();
    await controller.executePlan();
    const waiting = presentationFromFlow(controller.getSnapshot());
    expect(waiting.tasks[0]?.status).toBe("waiting");
    expect(waiting.consoleEvents.some((event) => event.status === "warning")).toBe(true);

    await controller.submitConfiguration(configurationValues(controller));
    const report = presentationFromFlow(controller.getSnapshot());
    expect(report.files.some((file) => file.active)).toBe(true);
    expect(report.files.some((file) => file.risk === 3)).toBe(true);

    await controller.openPatchReview();
    expect(presentationFromFlow(controller.getSnapshot()).mode).toBe("review");
    for (const patch of controller.getSnapshot().patchReview?.patches ?? []) {
      await controller.reviewPatch(patch.id, "accepted");
    }
    await controller.runInitialBuild();
    const failed = presentationFromFlow(controller.getSnapshot());
    expect(failed.tasks[0]?.status).toBe("failed");
    expect(failed.consoleEvents.some((event) => event.status === "failed")).toBe(true);
  });
});
