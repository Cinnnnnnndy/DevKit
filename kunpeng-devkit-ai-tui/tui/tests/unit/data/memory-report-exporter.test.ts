import { describe, expect, it } from "vitest";
import { MemoryReportExporter, MockDevKitGateway } from "../../../src/data/adapters/mock";

describe("MemoryReportExporter", () => {
  it("exports deterministic Markdown without touching the filesystem", async () => {
    const gateway = new MockDevKitGateway({ latencyMs: 0 });
    const summaryResult = await gateway.loadSessionSummary(
      "task-nginx-arm64",
      new AbortController().signal,
    );
    if (!summaryResult.ok) throw new Error(summaryResult.error.message);

    const exporter = new MemoryReportExporter();
    const result = await exporter.exportReport(
      {
        summary: summaryResult.value,
        format: "markdown",
        destinationPath: "reports/nginx.md",
      },
      new AbortController().signal,
    );

    expect(result).toMatchObject({
      ok: true,
      value: { destinationPath: "reports/nginx.md", format: "markdown" },
    });
    expect(exporter.read("reports/nginx.md")).toContain("# nginx x86_64 → Kunpeng ARM64");
  });

  it("does not export after cancellation", async () => {
    const exporter = new MemoryReportExporter();
    const gateway = new MockDevKitGateway({ latencyMs: 0 });
    const summaryResult = await gateway.loadSessionSummary(
      "task-nginx-arm64",
      new AbortController().signal,
    );
    if (!summaryResult.ok) throw new Error(summaryResult.error.message);

    const controller = new AbortController();
    controller.abort();
    const result = await exporter.exportReport(
      {
        summary: summaryResult.value,
        format: "json",
        destinationPath: "reports/nginx.json",
      },
      controller.signal,
    );
    expect(result).toMatchObject({ ok: false, error: { kind: "cancelled" } });
    expect(exporter.read("reports/nginx.json")).toBeUndefined();
  });
});
