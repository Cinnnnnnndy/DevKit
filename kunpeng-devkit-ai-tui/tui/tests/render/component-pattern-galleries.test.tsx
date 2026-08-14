import { afterAll, afterEach, beforeAll, describe, expect, it } from "bun:test";
import { testRender as rawTestRender } from "@opentui/react/test-utils";
import { act } from "react";
import { UiProvider } from "../../src/components/ui/index.js";
import { ComponentGallery } from "../../src/features/component-gallery/index.js";
import { PatternGallery } from "../../src/features/pattern-gallery/index.js";

Object.defineProperty(globalThis, "IS_REACT_ACT_ENVIRONMENT", {
  configurable: true,
  value: true,
  writable: true,
});
async function testRender(
  ...args: Parameters<typeof rawTestRender>
): Promise<Awaited<ReturnType<typeof rawTestRender>>> {
  let screen: Awaited<ReturnType<typeof rawTestRender>> | undefined;
  (
    globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT: boolean }
  ).IS_REACT_ACT_ENVIRONMENT = true;
  await act(async () => {
    screen = await rawTestRender(...args);
    await new Promise((resolve) => setTimeout(resolve, 0));
    await screen.flush({ maxPasses: 100 });
  });
  if (!screen) throw new Error("renderer did not initialize");
  return screen;
}

describe("component and pattern galleries", () => {
  const renderers: Array<{ destroy(): void | Promise<void> }> = [];
  let keeper: { destroy(): void | Promise<void> } | undefined;
  beforeAll(async () => {
    keeper = (await testRender(<box />, {})).renderer;
  });
  afterEach(async () => {
    await act(async () => {
      for (const renderer of renderers.splice(0)) {
        await renderer.destroy();
        (
          globalThis as typeof globalThis & { IS_REACT_ACT_ENVIRONMENT: boolean }
        ).IS_REACT_ACT_ENVIRONMENT = true;
      }
    });
  });
  afterAll(async () => {
    await act(async () => {
      await keeper?.destroy();
    });
  });

  it("renders and scrolls all 22 components at 160x50 and 58x32", async () => {
    for (const [width, height] of [
      [160, 50],
      [58, 32],
    ] as const) {
      const screen = await testRender(
        <UiProvider>
          <ComponentGallery width={width} height={height} />
        </UiProvider>,
        { width, height },
      );
      renderers.push(screen.renderer);
      expect(screen.captureCharFrame()).toContain("COMPONENTS");
      await act(async () => {
        screen.mockInput.pressKey("END");
        await screen.flush();
      });
      expect(screen.captureCharFrame()).toContain("Overlay");
    }
  });

  it("keeps pattern interaction semantics without color", async () => {
    const screen = await testRender(
      <UiProvider
        capabilities={{
          colorMode: "none",
          unicode: true,
          braille: true,
          mouse: true,
          ssh: false,
          animations: "none",
        }}
      >
        <PatternGallery
          width={58}
          height={32}
          initialSelected={20}
          initialFrozen
          initialRateIndex={1}
        />
      </UiProvider>,
      { width: 58, height: 32 },
    );
    renderers.push(screen.renderer);
    expect(screen.captureCharFrame()).toContain("Live Canvas");
    expect(screen.captureCharFrame()).toContain("Space freeze");
    expect(screen.captureCharFrame()).toContain("FROZEN");
    expect(screen.captureCharFrame()).toContain("500ms");
  });

  it("renders real P01, P13, and P20 component content", async () => {
    for (const [selected, needle] of [
      [0, "Understand Request"],
      [12, "qwen-72b"],
      [19, "Fork context"],
    ] as const) {
      const screen = await testRender(
        <UiProvider>
          <PatternGallery width={58} height={32} initialSelected={selected} />
        </UiProvider>,
        { width: 58, height: 32 },
      );
      renderers.push(screen.renderer);
      expect(screen.captureCharFrame()).toContain(needle);
    }
  });

  it("renders interactive P22-P26 states at narrow NO_COLOR", async () => {
    for (const [selected, needle] of [
      [21, "Kernel attention"],
      [22, "F1 Migrate"],
      [23, "sort value ↓"],
      [24, "selected=P25"],
      [25, "Heatmap Grid"],
    ] as const) {
      const screen = await testRender(
        <UiProvider
          capabilities={{
            colorMode: "none",
            unicode: true,
            braille: true,
            mouse: true,
            ssh: false,
            animations: "none",
          }}
        >
          <PatternGallery width={58} height={32} initialSelected={selected} />
        </UiProvider>,
        { width: 58, height: 32 },
      );
      renderers.push(screen.renderer);
      const frame = screen.captureCharFrame();
      expect(frame).toContain(needle);
      expect(frame.split("\n").every((line) => line.length <= 58)).toBe(true);
    }
  });
});
