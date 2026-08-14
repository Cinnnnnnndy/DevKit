import { describe, expect, it } from "vitest";
import {
  chartBox,
  fitPrimitive,
  PRIMITIVE_IDS,
  PRIMITIVE_SPECS,
  shrinkOrder,
} from "../../../src/components/charts/index.js";

describe("primitive layout registry", () => {
  it("locks the canonical seventeen primitives and dimensions", () => {
    expect(PRIMITIVE_IDS).toEqual([
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
    expect(PRIMITIVE_SPECS["metric-bar"]).toMatchObject({
      minimum: { width: 10, height: 1 },
      recommended: { width: 20, height: 1 },
      shrinkPriority: 1,
    });
    expect(PRIMITIVE_SPECS.flame).toMatchObject({
      minimum: { width: 30, height: 3 },
      recommended: { width: 60, height: 8 },
      shrinkPriority: 4,
      fallback: { kind: "layout", description: "Top-N hot-function table with percentages" },
    });
    expect(PRIMITIVE_SPECS.heatmap).toMatchObject({
      minimum: { width: 16, height: 4 },
      recommended: { width: 32, height: 6 },
      shrinkPriority: 4,
    });
  });

  it("normalizes outer boxes and derives drawable cells", () => {
    expect(chartBox(40.9, 12.8, { paddingX: 2, paddingY: 1, border: true })).toEqual({
      width: 40,
      height: 12,
      innerWidth: 34,
      innerHeight: 8,
    });
    expect(chartBox(Number.NaN, -1)).toEqual({
      width: 0,
      height: 0,
      innerWidth: 0,
      innerHeight: 0,
    });
  });

  it("classifies recommended, compact, minimum, and fallback fits", () => {
    expect(fitPrimitive("line", 40, 6).level).toBe("recommended");
    expect(fitPrimitive("line", 30, 5).level).toBe("compact");
    expect(fitPrimitive("line", 20, 3).level).toBe("minimum");
    expect(fitPrimitive("line", 19, 3)).toMatchObject({
      fits: false,
      level: "fallback",
      fallback: {
        kind: "primitive",
        primitive: "sparkline",
        description: "Sparkline plus latest value",
      },
    });
  });

  it("crops to aspect bands and enforces mirrored even rows", () => {
    expect(fitPrimitive("line", 100, 3).box).toEqual({ width: 72, height: 3 });
    expect(fitPrimitive("line", 20, 20).box).toEqual({ width: 20, height: 4 });
    expect(fitPrimitive("scatter", 40, 40).box).toEqual({ width: 40, height: 20 });
    expect(fitPrimitive("scatter", 40, 8).box).toEqual({ width: 16, height: 8 });
    expect(fitPrimitive("waterline", 20, 8).box).toEqual({ width: 6, height: 8 });
    expect(fitPrimitive("mirrored-area", 40, 5).box.height).toBe(4);
  });

  it("orders shrink candidates by priority, area, then input stability", () => {
    expect(
      shrinkOrder(["heatmap", "stat", "progress", "timeline", "line", "ranking"]).map(
        ({ id }) => id,
      ),
    ).toEqual(["stat", "progress", "ranking", "line", "timeline", "heatmap"]);

    const duplicateAreaA = { ...PRIMITIVE_SPECS.stat, id: "stat" as const };
    const duplicateAreaB = { ...PRIMITIVE_SPECS.stat, id: "stat" as const };
    expect(shrinkOrder([duplicateAreaA, duplicateAreaB])).toEqual([duplicateAreaA, duplicateAreaB]);
  });
});
