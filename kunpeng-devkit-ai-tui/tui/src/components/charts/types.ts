export type ColorMode = "truecolor" | "ansi16" | "none";

export type ChartCapabilities = {
  colorMode: ColorMode;
  braille: boolean;
  unicode: boolean;
};

export type ChartPalette = {
  background: string;
  border: string;
  text: string;
  white: string;
  blue: string;
  green: string;
  cyan: string;
  red: string;
  orange: string;
  yellow: string;
  empty: string;
  waterGreen: string;
  progressGreen: string;
  heatmap: readonly string[];
};

export type ChartBaseProps = {
  width: number;
  height: number;
  title?: string | undefined;
  palette?: Partial<ChartPalette> | undefined;
  capabilities?: Partial<ChartCapabilities> | undefined;
};

/** @deprecated Prefer ChartBaseProps in reusable chart APIs. */
export type ChartProps = ChartBaseProps;

export type ChartCell = {
  character: string;
  color?: string | undefined;
  background?: string | undefined;
};
