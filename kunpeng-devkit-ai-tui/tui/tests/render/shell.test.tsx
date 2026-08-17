import { afterAll, afterEach, beforeAll, describe, expect, it, mock } from "bun:test";
import { readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { testRender as rawTestRender } from "@opentui/react/test-utils";
import { act } from "react";
import { App } from "../../src/app/index.js";
import { colorProp } from "../../src/components/ui/color-props.js";
import { MockDevKitGateway } from "../../src/data/adapters/mock/index.js";
import { DEFAULT_TERMINAL_CAPABILITIES } from "../../src/platform/terminal/index.js";
import { tokensFor } from "../../src/theme/index.js";

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

describe("Style A native shell", () => {
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

  it("renders the wide 160x50 workbench with full Style A chrome", async () => {
    const screen = await testRender(
      <App
        gateway={new MockDevKitGateway({ latencyMs: 0 })}
        capabilities={DEFAULT_TERMINAL_CAPABILITIES}
        initialScreen="workbench"
      />,
      { width: 160, height: 50 },
    );
    renderers.push(screen.renderer);
    await screen.waitForFrame(
      (frame) => frame.includes("KUNPENG") && frame.includes("ACT 01 · ZERO-CONFIG LANDING"),
    );
    const frame = screen.captureCharFrame();
    if (process.env["DEVKITAI_WRITE_SHELL_FRAMES"] === "1")
      writeFileSync(
        fileURLToPath(new URL("./snapshots/shell/wide-160x50.txt", import.meta.url)),
        `${frame.trimEnd()}\n`,
        "utf8",
      );
    expect(frame).toContain("KUNPENG");
    expect(frame).toContain("ACT 01 · ZERO-CONFIG LANDING");
    expect(frame).toContain("Runtime 本地已就绪");
    expect(frame).not.toContain("PATCH PREVIEW");
    expect(frame).toContain("AGENT CONSOLE");
    expect(frame).toContain("Ctrl+P");
    expect(frame).toContain("mode:auto");
    expect(frame.split("\n").length).toBeLessThanOrEqual(51);
  });

  it("renders the deterministic pixel landing without workbench decoration", async () => {
    const stableCapabilities = {
      ...DEFAULT_TERMINAL_CAPABILITIES,
      animations: "none" as const,
    };
    const screen = await testRender(
      <App gateway={new MockDevKitGateway({ latencyMs: 0 })} capabilities={stableCapabilities} />,
      { width: 160, height: 50 },
    );
    renderers.push(screen.renderer);
    await screen.waitForFrame(
      (frame) =>
        frame.includes("AI TERMINAL") &&
        frame.includes("runtime") &&
        !frame.includes("Loading workspace"),
    );
    const frame = screen.captureCharFrame();
    const snapshotPath = fileURLToPath(
      new URL("./snapshots/shell/landing-160x50.txt", import.meta.url),
    );
    if (process.env["DEVKITAI_WRITE_SHELL_FRAMES"] === "1")
      writeFileSync(snapshotPath, `${frame.trimEnd()}\n`, "utf8");
    expect(`${frame.trimEnd()}\n`).toBe(readFileSync(snapshotPath, "utf8"));
    expect(frame).toContain("AI TERMINAL");
    expect(frame).toContain("NATIVE TUI");
    expect(frame).toContain("v26.0");
    expect(frame).toContain("KUNPENG ARM64");
    expect(frame).toContain("KUNPENG DEVKIT AI");
    expect(frame).toContain("2/4 已装载  cpp_migrator · knowledge_base");
    expect(frame).toContain("3 项能力未安装  [Enter] 查看");
    expect(frame).toContain("2 项待人工确认");
    expect(frame).toContain("想做什么？直接说 —— 例如「把 ./nginx 迁到鲲鹏」");
    expect(frame).toContain("Ctrl+P");
    expect(frame).toContain("命令面板");
    expect(frame).toContain("安装迁移能力包");
    expect(frame).toContain("扫描当前工程");
    expect(frame).toContain("继续上次任务");
    expect(frame).not.toContain("mock ports");
    expect(frame).not.toContain("1 迁移分析");
    expect(frame).not.toContain("AGENT CONSOLE");

    const spans = screen.captureSpans().lines.flatMap((line) => line.spans);
    const kpMark = spans.find((span) => span.text.includes("◢"));
    expect(kpMark).toBeDefined();
    expect(Array.from(kpMark?.fg.buffer ?? [])).toEqual([237, 28, 36, 255]);
    expect(
      spans.some(
        (span) =>
          span.text.includes("KUNPENG") &&
          [231, 231, 231, 255].every((value, index) => span.fg.buffer[index] === value),
      ),
    ).toBe(true);
  });

  it("keeps all five landing states, prompt and suggestions at 58x32", async () => {
    const screen = await testRender(
      <App
        gateway={new MockDevKitGateway({ latencyMs: 0 })}
        capabilities={{ ...DEFAULT_TERMINAL_CAPABILITIES, animations: "none" }}
      />,
      { width: 58, height: 32 },
    );
    renderers.push(screen.renderer);
    await screen.waitForFrame((frame) => frame.includes("继续上次任务"));
    const frame = screen.captureCharFrame();
    for (const scope of ["runtime", "toolchain", "mcp tools", "capabilities", "session"])
      expect(frame).toContain(scope);
    expect(frame).toContain("想做什么？直接说");
    expect(frame).toContain("安装迁移能力包");
    expect(frame).toContain("扫描当前工程");
    expect(frame).toContain("继续上次任务");
    expect(frame.split("\n").every((line) => [...line].length <= 58)).toBe(true);
  });

  it("degrades the landing deterministically across resize, ANSI16 and NO_COLOR", async () => {
    const ansi = await testRender(
      <App
        gateway={new MockDevKitGateway({ latencyMs: 0 })}
        capabilities={{
          ...DEFAULT_TERMINAL_CAPABILITIES,
          colorMode: "ansi16",
          animations: "none",
        }}
      />,
      { width: 160, height: 50 },
    );
    renderers.push(ansi.renderer);
    await ansi.waitForFrame(
      (frame) => frame.includes("KUNPENG DEVKIT AI") && frame.includes("AI TERMINAL"),
    );
    expect(
      ansi
        .captureSpans()
        .lines.flatMap((line) => line.spans)
        .some(
          (span) =>
            span.text.includes("◢") &&
            [255, 0, 0, 255].every((value, index) => span.fg.buffer[index] === value),
        ),
    ).toBe(true);
    await act(async () => {
      ansi.resize(58, 32);
      await ansi.flush({ maxPasses: 100 });
    });
    await act(async () => {
      await ansi.waitForFrame((frame) => frame.includes("KUNPENG DEVKIT AI"));
    });
    expect(ansi.captureCharFrame()).toContain("恢复 migrate nginx");
    await act(async () => {
      await ansi.renderer.destroy();
    });
    renderers.splice(renderers.indexOf(ansi.renderer), 1);

    const noColor = await testRender(
      <App
        gateway={new MockDevKitGateway({ latencyMs: 0 })}
        capabilities={{
          colorMode: "none",
          unicode: false,
          braille: false,
          mouse: false,
          ssh: true,
          animations: "none",
        }}
      />,
      { width: 58, height: 32 },
    );
    renderers.push(noColor.renderer);
    await act(async () => {
      await noColor.waitForFrame((frame) => frame.includes("继续上次任务"));
    });
    const first = noColor.captureCharFrame();
    await act(async () => {
      await noColor.flush({ maxPasses: 100 });
    });
    expect(noColor.captureCharFrame()).toBe(first);
    expect(first).toContain("runtime");
  });

  it("renders a 58x32 single-column shell without horizontal overflow", async () => {
    const screen = await testRender(
      <App
        gateway={new MockDevKitGateway({ latencyMs: 0 })}
        capabilities={DEFAULT_TERMINAL_CAPABILITIES}
        initialScreen="workbench"
      />,
      { width: 58, height: 32 },
    );
    renderers.push(screen.renderer);
    await screen.waitForFrame(
      (frame) => frame.includes("DEVKIT AI") && frame.includes("ACT 01 · ZERO-CONFIG LANDING"),
    );
    const frame = screen.captureCharFrame();
    if (process.env["DEVKITAI_WRITE_SHELL_FRAMES"] === "1")
      writeFileSync(
        fileURLToPath(new URL("./snapshots/shell/narrow-58x32.txt", import.meta.url)),
        `${frame.trimEnd()}\n`,
        "utf8",
      );
    expect(frame).toContain("DEVKIT AI");
    expect(frame).toContain("ACT 01 · ZERO-CONFIG LANDING");
    expect(frame).not.toContain("PATCH PREVIEW");
    expect(frame).not.toContain("INSPECTOR");
    expect(frame.split("\n").every((line) => [...line].length <= 58)).toBe(true);
  });

  it("opens command palette with the keyboard path", async () => {
    const screen = await testRender(
      <App
        gateway={new MockDevKitGateway({ latencyMs: 0 })}
        capabilities={DEFAULT_TERMINAL_CAPABILITIES}
        initialScreen="workbench"
      />,
      { width: 120, height: 40 },
    );
    renderers.push(screen.renderer);
    await screen.waitForFrame((frame) => frame.includes("ACT 01 · ZERO-CONFIG LANDING"));
    await act(async () => screen.mockInput.pressKey("p", { ctrl: true }));
    await screen.waitForFrame((frame) => frame.includes("COMMAND PALETTE"));
    expect(screen.captureCharFrame()).toContain("Complete config");
  });

  it("keeps keyboard focus and mouse task selection equivalent", async () => {
    const onIntent = mock(() => undefined);
    const screen = await testRender(
      <App
        gateway={new MockDevKitGateway({ latencyMs: 0 })}
        capabilities={DEFAULT_TERMINAL_CAPABILITIES}
        onIntent={onIntent}
      />,
      { width: 120, height: 40 },
    );
    renderers.push(screen.renderer);
    await screen.waitForFrame((frame) => frame.includes("AI TERMINAL"));
    await act(async () => {
      await screen.mockInput.typeText("分析当前项目");
      screen.mockInput.pressEnter();
    });
    expect(onIntent).toHaveBeenCalledWith("分析当前项目");
    await screen.waitForFrame((frame) => frame.includes("ACT 02 · EDITABLE AI PLAN"));
  });

  it("uses semantic glyphs when colors and unicode are unavailable", async () => {
    const capabilities = {
      colorMode: "none",
      unicode: false,
      braille: false,
      mouse: false,
      ssh: true,
      animations: "none",
    } as const;
    const screen = await testRender(
      <App
        gateway={new MockDevKitGateway({ latencyMs: 0 })}
        capabilities={capabilities}
        initialScreen="workbench"
      />,
      { width: 58, height: 32 },
    );
    renderers.push(screen.renderer);
    await screen.waitForFrame((frame) => frame.includes("ACT 01 · ZERO-CONFIG LANDING"));
    const frame = screen.captureCharFrame();
    expect(frame).toContain("CAPABILITIES");
    expect(frame).toContain("+ Local runtime ready");
    expect(frame).toContain("mode:auto");
    expect(frame).toContain("|ACT 01 · ZERO-CONFIG LANDING");

    const noColorTheme = tokensFor(capabilities);
    expect(noColorTheme.foreground).toBeUndefined();
    expect(noColorTheme.background).toBeUndefined();
    expect(noColorTheme.borderStrong).toBeUndefined();
    expect(colorProp("fg", noColorTheme.foreground)).toEqual({});
    expect(colorProp("backgroundColor", noColorTheme.background)).toEqual({});
    expect(colorProp("borderColor", noColorTheme.borderStrong)).toEqual({});

    // OpenTUI 的无样式文本和占位符使用默认值。NO_COLOR 不得在这些原生终端默认值之上
    // 叠加任何应用 RGB 颜色。
    const nativeDefaultForegrounds = new Set(["255,255,255,255", "102,102,102,255"]);

    const contentSpans = screen
      .captureSpans()
      .lines.flatMap((line) => line.spans)
      .filter((span) => span.text.trim().length > 0);
    expect(contentSpans.length).toBeGreaterThan(0);
    for (const span of contentSpans) {
      expect(nativeDefaultForegrounds.has(Array.from(span.fg.buffer).join(","))).toBe(true);
      expect(Array.from(span.bg.buffer)).toEqual([0, 0, 0, 0]);
    }
  });
});
