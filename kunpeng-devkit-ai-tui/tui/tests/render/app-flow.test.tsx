import { afterAll, afterEach, beforeAll, describe, expect, it } from "bun:test";
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { testRender as rawTestRender } from "@opentui/react/test-utils";
import { act } from "react";
import { App } from "../../src/app/index.js";
import { chartDisplayWidth } from "../../src/components/charts/chart-primitives.js";
import {
  type DelayScheduler,
  MemoryReportExporter,
  MockDevKitGateway,
  type ScheduledDelay,
} from "../../src/data/adapters/mock/index.js";
import type { DevKitGateway } from "../../src/data/ports/index.js";
import { DEFAULT_TERMINAL_CAPABILITIES } from "../../src/platform/terminal/index.js";
import { createAppError, err } from "../../src/shared/index.js";

Object.defineProperty(globalThis, "IS_REACT_ACT_ENVIRONMENT", {
  configurable: true,
  value: true,
  writable: true,
});

async function testRender(
  ...args: Parameters<typeof rawTestRender>
): Promise<Awaited<ReturnType<typeof rawTestRender>>> {
  let screen: Awaited<ReturnType<typeof rawTestRender>> | undefined;
  await act(async () => {
    screen = await rawTestRender(...args);
    await new Promise((resolve) => setTimeout(resolve, 30));
    await screen.flush({ maxPasses: 100 });
  });
  if (!screen) throw new Error("OpenTUI test renderer did not initialize");
  return screen;
}

class FlakyBootstrapGateway extends MockDevKitGateway {
  attempts = 0;

  override loadWorkspaceBootstrap(
    signal: AbortSignal,
  ): ReturnType<DevKitGateway["loadWorkspaceBootstrap"]> {
    this.attempts += 1;
    if (this.attempts === 1) {
      return Promise.resolve(
        err(createAppError("timeout", "test.bootstrap", "temporary timeout", true)),
      );
    }
    return super.loadWorkspaceBootstrap(signal);
  }
}

class BlockedBootstrapGateway extends MockDevKitGateway {
  attempts = 0;

  override loadWorkspaceBootstrap(
    _signal: AbortSignal,
  ): ReturnType<DevKitGateway["loadWorkspaceBootstrap"]> {
    this.attempts += 1;
    return Promise.resolve(
      err(createAppError("invalid-input", "test.blocked", "blocked request", false)),
    );
  }
}

async function pressAndWait(
  screen: Awaited<ReturnType<typeof rawTestRender>>,
  key: string,
  expected: string,
): Promise<void> {
  await act(async () => {
    if (key === "ENTER") screen.mockInput.pressEnter();
    else if (key === "ESCAPE") {
      screen.mockInput.pressEscape();
      await new Promise((resolve) => setTimeout(resolve, 60));
    } else screen.mockInput.pressKey(key);
  });
  await screen.waitForFrame((frame) => frame.includes(expected));
}

type AppTestScreen = Awaited<ReturnType<typeof rawTestRender>>;
type CapturedActFrame = { readonly label: string; readonly frame: string };

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

async function runTenActFlow(screen: AppTestScreen): Promise<readonly CapturedActFrame[]> {
  const frames: CapturedActFrame[] = [];
  const capture = (label: string): void => {
    frames.push({ label, frame: screen.captureCharFrame() });
  };
  await screen.waitForFrame((frame) => frame.includes("AI TERMINAL"));
  capture("ACT 01 · ZERO-CONFIG LANDING");

  await act(async () => {
    await screen.mockInput.typeText("把 ./nginx 迁移到鲲鹏 ARM64 并完成性能验证");
    screen.mockInput.pressEnter();
  });
  await screen.waitForFrame((frame) => frame.includes("ACT 02 · EDITABLE AI PLAN"));
  await pressAndWait(screen, "m", "v2 · 5 steps");
  capture("ACT 02 · EDITABLE AI PLAN");

  await pressAndWait(screen, "ENTER", "补充配置");
  capture("ACT 03 · CONFIG COMPLETION OVERLAY");
  await pressAndWait(screen, "ENTER", "ACT 04 · COMPATIBILITY REPORT");
  capture("ACT 04 · COMPATIBILITY REPORT");
  if (screen.captureCharFrame().includes("PROJECT · FOLLOW")) {
    expect(screen.captureCharFrame()).toMatch(/src\/crypto\.c\s+███/u);
    expect(screen.captureCharFrame()).not.toContain("src/crypto.c███");
  }
  await pressAndWait(screen, "ENTER", "ACT 05 · PATCH & EVIDENCE REVIEW");
  for (let patch = 0; patch < 2; patch += 1) {
    await pressAndWait(screen, "a", "APPLY APPROVAL");
    await act(async () => screen.mockInput.pressEnter());
    await screen.waitForFrame((frame) => frame.includes(`${patch + 1} accepted`));
  }
  capture("ACT 05 · PATCH & EVIDENCE REVIEW");

  await pressAndWait(screen, "b", "BUILD FAILED");
  capture("ACT 06A · BUILD FAILED");
  await pressAndWait(screen, "ENTER", "ROOT CAUSE");
  capture("ACT 06B · ROOT CAUSE & EVIDENCE");
  await pressAndWait(screen, "ENTER", "BUILD PASS");
  capture("ACT 06C · FIXED & VERIFIED");

  await pressAndWait(screen, "ENTER", "ACT 07 · PERFORMANCE BASELINE");
  capture("ACT 07 · PERFORMANCE BASELINE");
  await pressAndWait(screen, "ENTER", "ACT 08 · TUNING PLAN COMPARISON");
  await pressAndWait(screen, "ENTER", "✓ Applied");
  capture("ACT 08 · TUNING APPLIED");
  await pressAndWait(screen, "ENTER", "ACT 09 · SCENARIO PROFILE");
  await pressAndWait(screen, "ENTER", "连接建立耗时下降");
  capture("ACT 09 · SCENARIO PROFILE VERIFIED");
  await pressAndWait(screen, "ENTER", "ACT 10 · SESSION SUMMARY");
  await pressAndWait(screen, "s", "Report saved: reports/nginx-migration.md");
  capture("ACT 10 · SUMMARY & EXPORTED REPORT");
  return frames;
}

function writeFrames(relativePath: string, frames: readonly CapturedActFrame[]): void {
  if (process.env["DEVKITAI_WRITE_FLOW_FRAMES"] !== "1") return;
  const content = frames
    .map(({ label, frame }) => `===== ${label} =====\n${frame.trimEnd()}`)
    .join("\n\n");
  writeFileSync(fileURLToPath(new URL(relativePath, import.meta.url)), `${content}\n`, "utf8");
}

describe("formal App ten-act integration", () => {
  const renderers: Array<{ destroy(): void | Promise<void> }> = [];
  let keeper: { destroy(): void | Promise<void> } | undefined;

  beforeAll(async () => {
    keeper = (await testRender(<box />, {})).renderer;
  });

  afterEach(async () => {
    await act(async () => {
      for (const renderer of renderers.splice(0)) await renderer.destroy();
    });
  });

  afterAll(async () => {
    await keeper?.destroy();
  });

  it("completes all ten acts through keyboard actions and exports the summary", async () => {
    const exporter = new MemoryReportExporter();
    const screen = await testRender(
      <App
        gateway={new MockDevKitGateway({ latencyMs: 0 })}
        reportExporter={exporter}
        capabilities={DEFAULT_TERMINAL_CAPABILITIES}
      />,
      { width: 160, height: 50 },
    );
    renderers.push(screen.renderer);
    const frames = await runTenActFlow(screen);
    writeFrames("./snapshots/app-flow/wide-160x50.txt", frames);

    expect(exporter.read("reports/nginx-migration.md")).toContain("Build: PASSED");
    expect(frames).toHaveLength(12);
    const combinedFrames = frames.map(({ frame }) => frame).join("\n");
    expect(combinedFrames).not.toMatch(/[鎵褰锛鈥]/u);
    expect(combinedFrames).not.toMatch(/配置0·0CPU9/u);
    expect(combinedFrames).toContain("激进低延迟配置 · CPU 占用升至 88% · 内存增加至 6.8 GiB");
  });

  it("keeps the same ten-act path readable at 58x32", async () => {
    const exporter = new MemoryReportExporter();
    const screen = await testRender(
      <App
        gateway={new MockDevKitGateway({ latencyMs: 0 })}
        reportExporter={exporter}
        capabilities={DEFAULT_TERMINAL_CAPABILITIES}
      />,
      { width: 58, height: 32 },
    );
    renderers.push(screen.renderer);
    const frames = await runTenActFlow(screen);
    writeFrames("./snapshots/app-flow/narrow-58x32.txt", frames);
    expect(frames).toHaveLength(12);
    expect(
      frames.every(({ frame }) => frame.split("\n").every((line) => chartDisplayWidth(line) <= 58)),
    ).toBe(true);
    const summaryFrame = frames.at(-1)?.frame ?? "";
    const planFrame = frames.find(({ label }) => label.startsWith("ACT 02"))?.frame ?? "";
    expect(planFrame).not.toContain("...eng_knowledge_base_search");
    expect(summaryFrame).toContain("nginx x86_64 → Kunpeng ARM64");
    expect(summaryFrame).toContain("✓ 21 fixed · ⚠ 2 manual · Build PASSED");
    expect(summaryFrame).toContain("MODIFIED FILES");
    expect(summaryFrame).not.toMatch(/✓g|·Osrc/u);
  });

  it("opens /chart from the prompt and returns to the previous screen", async () => {
    const screen = await testRender(
      <App
        gateway={new MockDevKitGateway({ latencyMs: 0 })}
        capabilities={DEFAULT_TERMINAL_CAPABILITIES}
      />,
      { width: 58, height: 32 },
    );
    renderers.push(screen.renderer);
    await screen.waitForFrame((frame) => frame.includes("AI TERMINAL"));
    await act(async () => {
      await screen.mockInput.typeText("/chart");
      screen.mockInput.pressEnter();
    });
    await screen.waitForFrame((frame) => frame.includes("图表原语库"));
    await act(async () => screen.mockInput.pressKey("END"));
    await screen.waitForFrame((frame) => frame.includes("17 · Heatmap"));
    await act(async () => {
      screen.mockInput.pressEscape();
      await new Promise((resolve) => setTimeout(resolve, 60));
    });
    await screen.waitForFrame((frame) => frame.includes("AI TERMINAL"));
  });

  it("opens /components from the landing prompt and returns with Esc", async () => {
    const screen = await testRender(
      <App
        gateway={new MockDevKitGateway({ latencyMs: 0 })}
        capabilities={DEFAULT_TERMINAL_CAPABILITIES}
      />,
      { width: 100, height: 38 },
    );
    renderers.push(screen.renderer);
    await screen.waitForFrame((frame) => frame.includes("AI TERMINAL"));
    await act(async () => {
      await screen.mockInput.typeText("/components");
      screen.mockInput.pressEnter();
    });
    await screen.waitForFrame((frame) => frame.includes("组件清单"));
    await act(async () => {
      screen.mockInput.pressEscape();
      await new Promise((resolve) => setTimeout(resolve, 60));
    });
    await screen.waitForFrame((frame) => frame.includes("AI TERMINAL"));
  });

  it("opens /patterns from the landing prompt and returns with Esc", async () => {
    const screen = await testRender(
      <App
        gateway={new MockDevKitGateway({ latencyMs: 0 })}
        capabilities={DEFAULT_TERMINAL_CAPABILITIES}
      />,
      { width: 100, height: 38 },
    );
    renderers.push(screen.renderer);
    await screen.waitForFrame((frame) => frame.includes("AI TERMINAL"));
    await act(async () => {
      await screen.mockInput.typeText("/patterns");
      screen.mockInput.pressEnter();
    });
    await screen.waitForFrame((frame) => frame.includes("Understand Request"));
    await act(async () => {
      screen.mockInput.pressEscape();
      await new Promise((resolve) => setTimeout(resolve, 60));
    });
    await screen.waitForFrame((frame) => frame.includes("AI TERMINAL"));
  });

  it("cancels an in-flight operation with Esc and retries it with R", async () => {
    const scheduler = new ManualDelayScheduler();
    const screen = await testRender(
      <App
        gateway={new MockDevKitGateway({ scenario: "slow", latencyMs: 90, scheduler })}
        capabilities={DEFAULT_TERMINAL_CAPABILITIES}
        initialScreen="workbench"
      />,
      { width: 100, height: 38 },
    );
    renderers.push(screen.renderer);
    await screen.waitForFrame((frame) => frame.includes("workspace.bootstrap"));
    await pressAndWait(screen, "ESCAPE", "操作已取消");
    expect(scheduler.pendingCount).toBe(0);
    await act(async () => {
      screen.mockInput.pressKey("r");
    });
    expect(scheduler.pendingCount).toBe(1);
    await act(async () => scheduler.runAll());
    await screen.waitForFrame((frame) => frame.includes("Runtime 本地已就绪"));
  });

  it("recovers a retryable bootstrap failure without losing the workbench", async () => {
    const flaky = new FlakyBootstrapGateway({ latencyMs: 0 });
    const screen = await testRender(
      <App
        gateway={flaky}
        capabilities={DEFAULT_TERMINAL_CAPABILITIES}
        initialScreen="workbench"
      />,
      { width: 100, height: 38 },
    );
    renderers.push(screen.renderer);
    await screen.waitForFrame((frame) => frame.includes("temporary timeout"));
    await pressAndWait(screen, "r", "Runtime 本地已就绪");
    expect(flaky.attempts).toBe(2);
  });

  it("does not offer or accept R when the current error is non-retryable", async () => {
    const gateway = new BlockedBootstrapGateway({ latencyMs: 0 });
    const screen = await testRender(
      <App
        gateway={gateway}
        capabilities={DEFAULT_TERMINAL_CAPABILITIES}
        initialScreen="workbench"
      />,
      { width: 100, height: 38 },
    );
    renderers.push(screen.renderer);
    await screen.waitForFrame((frame) => frame.includes("blocked request"));
    expect(screen.captureCharFrame()).not.toContain("R 重试");

    await act(async () => screen.mockInput.pressKey("r"));
    await screen.flush({ maxPasses: 20 });

    expect(gateway.attempts).toBe(1);
    expect(screen.captureCharFrame()).toContain("blocked request");
  });
});
