import type { ChartCapabilities, ChartPalette } from "./types.js";

/**
 * Palette sampled from the approved command-line chart reference.
 *
 * Keep this independent from application styling: consumers may inject a
 * domain palette through `palette` without changing the reference contract.
 */
export const REFERENCE_CHART_PALETTE: ChartPalette = {
  background: "#000000",
  border: "#42474D",
  text: "#C1C1C1",
  white: "#FFFFFF",
  blue: "#0071E7",
  green: "#4B911F",
  cyan: "#2BB8C9",
  red: "#B93737",
  orange: "#F69F38",
  yellow: "#EDAF28",
  empty: "#25282C",
  waterGreen: "#24AB35",
  progressGreen: "#229432",
  heatmap: ["#013D85", "#166FCB", "#5DA3E9", "#B7DAF8", "#ECF6FD"],
};

export const DEFAULT_CHART_CAPABILITIES: ChartCapabilities = {
  colorMode: "truecolor",
  braille: true,
  unicode: true,
};

const ANSI16_CHART_PALETTE: ChartPalette = {
  background: "#000000",
  border: "#808080",
  text: "#C0C0C0",
  white: "#FFFFFF",
  blue: "#0000FF",
  green: "#008000",
  cyan: "#00FFFF",
  red: "#800000",
  orange: "#FFFF00",
  yellow: "#FFFF00",
  empty: "#808080",
  waterGreen: "#008000",
  progressGreen: "#008000",
  heatmap: ["#000080", "#0000FF", "#008080", "#00FFFF", "#FFFFFF"],
};

export function resolveChartPalette(
  palette?: Partial<ChartPalette>,
  capabilities?: Partial<ChartCapabilities>,
): ChartPalette {
  const base =
    capabilities?.colorMode === "ansi16" ? ANSI16_CHART_PALETTE : REFERENCE_CHART_PALETTE;
  return { ...base, ...palette, heatmap: palette?.heatmap ?? base.heatmap };
}

export function resolveChartCapabilities(
  capabilities?: Partial<ChartCapabilities>,
): ChartCapabilities {
  return { ...DEFAULT_CHART_CAPABILITIES, ...capabilities };
}
