import { afterAll, afterEach, beforeAll, describe, expect, it } from "bun:test";
import type { CapturedFrame, ScrollBoxRenderable } from "@opentui/core";
import { testRender as rawTestRender } from "@opentui/react/test-utils";
import { act } from "react";
import { chartDisplayWidth } from "../../../src/components/charts/chart-primitives.js";
import {
  AreaChart,
  BarChart,
  FlameChart,
  GroupedBarChart,
  HeatmapChart,
  LineChart,
  ProgressChart,
  ScatterChart,
  TreeChart,
  WaterlineChart,
} from "../../../src/components/charts/index.js";
import { CHART_GALLERY_ITEMS, ChartGallery } from "../../../src/features/chart-gallery/index.js";

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
    await new Promise((resolve) => setTimeout(resolve, 0));
    await screen.flush({ maxPasses: 100 });
  });
  if (!screen) throw new Error("OpenTUI test renderer did not initialize");
  return screen;
}

function hasSpanColor(
  frame: CapturedFrame,
  rgb: readonly [number, number, number],
  channel: "fg" | "bg",
): boolean {
  return frame.lines.some((line) =>
    line.spans.some((span) => rgb.every((value, index) => span[channel].buffer[index] === value)),
  );
}

function backgroundLineIndices(
  frame: CapturedFrame,
  rgb: readonly [number, number, number],
): number[] {
  return frame.lines.flatMap((line, index) =>
    line.spans.some((span) => rgb.every((value, channel) => span.bg.buffer[channel] === value))
      ? [index]
      : [],
  );
}

function coloredCellCountAtLine(
  frame: CapturedFrame,
  needle: string,
  rgb: readonly [number, number, number],
  channel: "fg" | "bg" = "fg",
): number {
  const line = frame.lines.find((candidate) =>
    candidate.spans.some((span) => span.text.includes(needle)),
  );
  return (
    line?.spans.reduce(
      (total, span) =>
        total +
        (rgb.every((value, index) => span[channel].buffer[index] === value)
          ? chartDisplayWidth(span.text)
          : 0),
      0,
    ) ?? 0
  );
}

function longestRun(text: string, pattern: RegExp): number {
  return Math.max(0, ...Array.from(text.matchAll(pattern), (match) => chartDisplayWidth(match[0])));
}

describe("chart OpenTUI rendering", () => {
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

  it("mounts exactly seventeen scrollable sections at 160x50", async () => {
    const screen = await testRender(<ChartGallery width={160} height={50} />, {
      width: 160,
      height: 50,
    });
    renderers.push(screen.renderer);
    for (const item of CHART_GALLERY_ITEMS) {
      expect(screen.renderer.root.findDescendantById(`chart-section-${item.id}`)).toBeDefined();
    }
    const gallery = screen.renderer.root.findDescendantById("chart-gallery-scroll") as
      | ScrollBoxRenderable
      | undefined;
    expect(gallery).toBeDefined();
    await act(async () => {
      screen.mockInput.pressKey("END");
    });
    const frame = await screen.waitForFrame((value) => value.includes("17 · Heatmap"));
    expect(frame.split("\n").every((line) => chartDisplayWidth(line.trimEnd()) <= 160)).toBe(true);
  });

  it("keeps the same order and scroll path at 58x32", async () => {
    const screen = await testRender(<ChartGallery width={58} height={32} />, {
      width: 58,
      height: 32,
    });
    renderers.push(screen.renderer);
    expect(screen.captureCharFrame()).toContain("01 · Metric Bar");
    const gallery = screen.renderer.root.findDescendantById("chart-gallery-scroll") as
      | ScrollBoxRenderable
      | undefined;
    expect(gallery).toBeDefined();
    await act(async () => {
      screen.mockInput.pressArrow("down");
      screen.mockInput.pressKey("\u001b[6~");
      screen.mockInput.pressKey("END");
    });
    const frame = await screen.waitForFrame((value) => value.includes("17 · Heatmap"));
    expect(frame.split("\n").every((line) => chartDisplayWidth(line.trimEnd()) <= 58)).toBe(true);
  });

  it("renders reference TrueColor and nearest ANSI16 colors", async () => {
    const trueColor = await testRender(
      <box width="100%" height="100%" flexDirection="column">
        <GroupedBarChart width={80} height={15} data={[{ label: "A", values: [100, 70, 40] }]} />
        <HeatmapChart
          width={80}
          height={13}
          data={[{ label: "范围", values: [0, 25, 50, 75, 100] }]}
        />
      </box>,
      { width: 80, height: 30 },
    );
    renderers.push(trueColor.renderer);
    expect(hasSpanColor(trueColor.captureSpans(), [0, 113, 231], "fg")).toBe(true);
    expect(
      hasSpanColor(trueColor.captureSpans(), [1, 61, 133], "fg") ||
        hasSpanColor(trueColor.captureSpans(), [1, 61, 133], "bg"),
    ).toBe(true);
    expect(
      hasSpanColor(trueColor.captureSpans(), [236, 246, 253], "fg") ||
        hasSpanColor(trueColor.captureSpans(), [236, 246, 253], "bg"),
    ).toBe(true);

    const ansi16 = await testRender(
      <GroupedBarChart
        width={72}
        height={12}
        capabilities={{ colorMode: "ansi16" }}
        data={[{ label: "A", values: [100, 60, 30] }]}
      />,
      { width: 72, height: 12 },
    );
    renderers.push(ansi16.renderer);
    expect(hasSpanColor(ansi16.captureSpans(), [0, 0, 255], "fg")).toBe(true);
    expect(hasSpanColor(ansi16.captureSpans(), [0, 113, 231], "fg")).toBe(false);
  });

  it("retains shape semantics without color, Braille, or Unicode", async () => {
    const none = { colorMode: "none" as const, braille: false, unicode: false };
    const screen = await testRender(
      <box width="100%" height="100%" flexDirection="column">
        <GroupedBarChart
          width={72}
          height={12}
          capabilities={none}
          data={[{ label: "A", values: [100, 60, 30] }]}
        />
        <ScatterChart
          width={72}
          height={10}
          capabilities={none}
          data={[
            { x: 1, y: 1, tone: "red" },
            { x: 2, y: 2, tone: "green" },
          ]}
        />
        <HeatmapChart
          width={72}
          height={8}
          capabilities={none}
          data={[{ label: "ASCII", values: [0, 25, 50, 75, 100] }]}
        />
      </box>,
      { width: 72, height: 32 },
    );
    renderers.push(screen.renderer);
    const text = screen.captureCharFrame();
    const spans = screen.captureSpans();
    expect(text).toContain("#");
    expect(text).toMatch(/[+|.-]/u);
    for (const rgb of [
      [0, 113, 231],
      [1, 61, 133],
      [236, 246, 253],
    ] as const) {
      expect(hasSpanColor(spans, rgb, "fg") || hasSpanColor(spans, rgb, "bg")).toBe(false);
    }
  });

  it("renders the complete gallery chrome without color attributes", async () => {
    const screen = await testRender(
      <ChartGallery
        width={72}
        height={32}
        capabilities={{ colorMode: "none", braille: false, unicode: false }}
      />,
      { width: 72, height: 32 },
    );
    renderers.push(screen.renderer);
    await screen.waitForFrame(
      (frame) => frame.includes("图表原语库") && frame.includes("Metric Bar"),
    );

    const frame = screen.captureCharFrame();
    expect(frame).toContain("单列 / 17 种");
    expect(frame).toContain("Ranking");

    const contentSpans = screen
      .captureSpans()
      .lines.flatMap((line) => line.spans)
      .filter((span) => span.text.trim().length > 0);
    expect(contentSpans.length).toBeGreaterThan(0);
    for (const span of contentSpans) {
      expect(Array.from(span.fg.buffer)).toEqual([255, 255, 255, 255]);
      expect(Array.from(span.bg.buffer)).toEqual([0, 0, 0, 0]);
    }
  });

  it("locks flame, area, waterline, and progress reference contracts", async () => {
    const tones = ["red", "green", "cyan", "orange"] as const;
    const flame = await testRender(
      <FlameChart
        width={88}
        height={28}
        title="FlameContract"
        data={Array.from({ length: 20 }, (_, index) => [
          {
            label: "SensitiveBusinessLabel",
            start: 0,
            end: 100,
            tone: tones.at(index % tones.length) ?? "orange",
          },
        ])}
      />,
      { width: 88, height: 28 },
    );
    renderers.push(flame.renderer);
    expect(flame.captureCharFrame()).not.toContain("SensitiveBusinessLabel");
    expect(flame.captureCharFrame()).not.toContain("100%");
    const coloredRows = new Set([
      ...backgroundLineIndices(flame.captureSpans(), [185, 55, 55]),
      ...backgroundLineIndices(flame.captureSpans(), [75, 145, 31]),
      ...backgroundLineIndices(flame.captureSpans(), [43, 184, 201]),
      ...backgroundLineIndices(flame.captureSpans(), [246, 159, 56]),
    ]);
    expect(coloredRows.size).toBe(20);

    const area = await testRender(
      <AreaChart
        width={88}
        height={14}
        title="AreaContract"
        data={[
          { label: "08:00", value: 20 },
          { label: "12:00", value: 73 },
          { label: "16:00", value: 35 },
          { label: "20:00", value: 60 },
        ]}
      />,
      { width: 88, height: 14 },
    );
    renderers.push(area.renderer);
    const areaText = area.captureCharFrame();
    expect(areaText).toContain("100");
    expect(areaText).toContain("08:00");
    expect(areaText).toContain("20:00");

    const water = await testRender(
      <WaterlineChart
        width={96}
        height={24}
        data={[
          { label: "DST_1", value: 100 },
          { label: "DST_2", value: 60 },
          { label: "RMA_Die_100", value: 0 },
        ]}
      />,
      { width: 96, height: 24 },
    );
    renderers.push(water.renderer);
    expect(water.captureCharFrame()).not.toContain("░");
    expect(
      water
        .captureCharFrame()
        .split("\n")
        .filter((line) => line.includes("▪")),
    ).toHaveLength(8);

    const labels = ["DST_1", "DST_2", "DST_3", "DST_4", "DST_5", "DST_6", "RMA_Die_100"];
    const progress = await testRender(
      <ProgressChart
        width={100}
        height={14}
        title="ProgressContract"
        data={labels.map((label) => ({
          label,
          value: 50,
          status: "STATUS_MUST_NOT_RENDER",
        }))}
      />,
      { width: 100, height: 14 },
    );
    renderers.push(progress.renderer);
    const progressText = progress.captureCharFrame();
    expect(progressText).not.toContain("STATUS_MUST_NOT_RENDER");
    const firstRow = progressText.split("\n").find((line) => line.includes("DST_1")) ?? "";
    expect(chartDisplayWidth(firstRow.match(/\[([^\]]*)\]/u)?.[1] ?? "")).toBe(36);
    expect(coloredCellCountAtLine(progress.captureSpans(), "DST_1", [34, 148, 50])).toBe(9);
    expect(coloredCellCountAtLine(progress.captureSpans(), "DST_1", [237, 175, 40])).toBe(7);
    expect(coloredCellCountAtLine(progress.captureSpans(), "DST_1", [185, 55, 55])).toBe(2);
    expect(coloredCellCountAtLine(progress.captureSpans(), "DST_1", [37, 40, 44])).toBe(18);
  });

  it("bounds edge cases, 10k data, and dynamic resize", async () => {
    const largeArea = Array.from({ length: 10_000 }, (_, index) => ({
      label: `很长的中文采样标签-${index}`,
      value: index % 97 === 0 ? Number.NaN : index % 2 ? -5 : 5,
    }));
    const screen = await testRender(
      <box width="100%" height="100%" flexDirection="column">
        <BarChart width={58} height={8} data={[]} />
        <LineChart
          width={58}
          height={11}
          data={[
            { label: "超长中文单点序列名称", tone: "green", values: [-5] },
            { label: "等值与非数值序列", tone: "orange", values: [3, 3, Number.NaN] },
          ]}
        />
        <AreaChart width={58} height={11} data={largeArea} />
        <TreeChart
          width={58}
          height={8}
          data={[{ id: "root", label: "超长中文根节点名称用于验证安全截断", children: [] }]}
        />
      </box>,
      { width: 58, height: 40 },
    );
    renderers.push(screen.renderer);
    expect(screen.captureCharFrame()).not.toMatch(/NaN|Infinity/u);
    expect(
      screen
        .captureCharFrame()
        .split("\n")
        .every((line) => chartDisplayWidth(line.trimEnd()) <= 58),
    ).toBe(true);
    await act(async () => {
      screen.resize(160, 50);
      await screen.flush({ maxPasses: 100 });
    });
    expect(screen.captureCharFrame()).not.toMatch(/NaN|Infinity/u);
    expect(
      screen
        .captureCharFrame()
        .split("\n")
        .every((line) => chartDisplayWidth(line.trimEnd()) <= 160),
    ).toBe(true);

    const dense = await testRender(
      <AreaChart
        width={88}
        height={14}
        data={Array.from({ length: 640 }, (_, index) => ({
          label: index === 0 ? "08:00" : index === 639 ? "20:00" : "12:00",
          value: index % 2 === 0 ? 0 : 100,
        }))}
      />,
      { width: 88, height: 14 },
    );
    renderers.push(dense.renderer);
    const topLine =
      dense
        .captureCharFrame()
        .split("\n")
        .find((line) => line.includes("100")) ?? "";
    expect(longestRun(topLine, /[█▄#]+/gu)).toBeLessThanOrEqual(4);
  });
});
