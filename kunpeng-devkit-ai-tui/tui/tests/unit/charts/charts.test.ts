import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import * as publicCharts from "../../../src/components/charts/index.js";
import {
  chartDisplayWidth,
  createBraillePixels,
  drawBrailleSegment,
  fitChartText,
} from "../../../src/components/charts/chart-primitives.js";
import { resolveChartPalette } from "../../../src/components/charts/palette.js";
import { CHART_GALLERY_ITEMS } from "../../../src/features/chart-gallery/index.js";
import { chartGalleryFixtures } from "../../../src/features/chart-gallery/fixtures.js";

describe("reusable chart boundary", () => {
  it("exposes exactly seventeen canonical charts in the approved order", () => {
    expect(CHART_GALLERY_ITEMS.map((item) => item.id)).toEqual([
      "metric-bar",
      "ranking",
      "grouped-bar",
      "before-after",
      "line",
      "area",
      "sparkline",
      "mirrored-area",
      "scatter",
      "flame",
      "timeline",
      "waterline",
      "progress",
      "segmented",
      "pixel-number",
      "stat",
      "heatmap",
    ]);
    expect(new Set(CHART_GALLERY_ITEMS.map((item) => item.id))).toHaveLength(17);
  });

  it("keeps internal helpers and fixtures out of the production barrel", () => {
    expect(Object.keys(publicCharts)).toEqual(
      expect.arrayContaining([
        "ChartFrame",
        "MetricBar",
        "RankingChart",
        "GroupedBarChart",
        "BeforeAfterChart",
        "ScatterChart",
        "LineChart",
        "FlameChart",
        "AreaChart",
        "SparklineChart",
        "MirroredAreaChart",
        "TimelineChart",
        "WaterlineChart",
        "ProgressChart",
        "SegmentedChart",
        "HeatmapChart",
        "PixelNumberChart",
        "StatChart",
        "REFERENCE_CHART_PALETTE",
      ]),
    );
    expect(publicCharts).not.toHaveProperty("CellLine");
    expect(publicCharts).not.toHaveProperty("chartDisplayWidth");
    expect(publicCharts).not.toHaveProperty("resolveChartPalette");
    expect(publicCharts).not.toHaveProperty("chartGalleryFixtures");
  });

  it("contains no imports across the charts copy boundary", () => {
    const chartsDirectory = fileURLToPath(
      new URL("../../../src/components/charts/", import.meta.url),
    );
    const sources = readdirSync(chartsDirectory)
      .filter((name) => /\.(?:ts|tsx)$/u.test(name))
      .map((name) => readFileSync(`${chartsDirectory}/${name}`, "utf8"));

    expect(sources).toHaveLength(20);
    for (const source of sources) {
      const specifiers = Array.from(
        source.matchAll(/\bfrom\s+["']([^"']+)["']/gu),
        (match) => match[1],
      );
      expect(
        specifiers.every((specifier) => specifier === "react" || specifier?.startsWith("./")),
      ).toBe(true);
      expect(source).not.toMatch(/Math\.random|demo-data|features\/|theme|gateway|service/iu);
    }
  });

  it("locks the reference and ANSI16 palette endpoints", () => {
    expect(publicCharts.REFERENCE_CHART_PALETTE.blue).toBe("#0071E7");
    expect(publicCharts.REFERENCE_CHART_PALETTE.progressGreen).toBe("#229432");
    expect(publicCharts.REFERENCE_CHART_PALETTE.heatmap).toEqual([
      "#013D85",
      "#166FCB",
      "#5DA3E9",
      "#B7DAF8",
      "#ECF6FD",
    ]);
    expect(resolveChartPalette(undefined, { colorMode: "ansi16" }).blue).toBe("#0000FF");
  });

  it("measures and truncates CJK by terminal display width", () => {
    expect(chartDisplayWidth("CPU 图表")).toBe(8);
    expect(fitChartText("构建耗时", 6)).toBe("构建耗");
    expect(chartDisplayWidth(fitChartText("构建耗时", 9))).toBe(9);
  });

  it("draws bounded Braille segments", () => {
    const pixels = createBraillePixels(12, 4);
    drawBrailleSegment(pixels, { x: 0, y: 15 }, { x: 23, y: 0 });
    const masks = pixels.flat().filter((mask) => mask > 0);
    expect(masks.length).toBeGreaterThan(5);
    expect(masks.every((mask) => mask <= 0xff)).toBe(true);
  });

  it("keeps gallery fixtures deterministic and outside render code", () => {
    expect(JSON.stringify(chartGalleryFixtures)).toBe(JSON.stringify(chartGalleryFixtures));
    expect(chartGalleryFixtures.flame).toHaveLength(20);
    expect(chartGalleryFixtures.digitalNumber).toBe("89:01234567");
  });
});
