export type { ChartBaseProps, ChartCapabilities, ChartPalette, ColorMode } from "./types.js";
export { DEFAULT_CHART_CAPABILITIES, REFERENCE_CHART_PALETTE } from "./palette.js";
export type {
  ChartBox,
  ChartBoxOptions,
  PrimitiveFallback,
  PrimitiveAspect,
  PrimitiveFitLevel,
  PrimitiveFitResult,
  PrimitiveId,
  PrimitiveSize,
  PrimitiveSpec,
  PrimitiveTier,
} from "./primitive-layout.js";
export {
  chartBox,
  fitPrimitive,
  PRIMITIVE_IDS,
  PRIMITIVE_SPECS,
  shrinkOrder,
} from "./primitive-layout.js";

export { ChartFrame } from "./ChartFrame.js";
export type {
  ChartAxis,
  ChartFrameLayout,
  ChartFrameProps,
  ChartLegendItem,
} from "./ChartFrame.js";

export { BarChart } from "./BarChart.js";
export type { BarChartDatum, BarChartProps } from "./BarChart.js";
export type { GroupedBarChartDatum } from "./GroupedBarChart.js";
export { DivergingBarChart } from "./DivergingBarChart.js";
export type { DivergingBarChartDatum, DivergingBarChartProps } from "./DivergingBarChart.js";
export type { ScatterDatum, ScatterTone } from "./ScatterChart.js";
export type { LineSeries, LineTone } from "./LineChart.js";
export type { FlameSpan, FlameTone } from "./FlameChart.js";
export type { AreaDatum } from "./AreaChart.js";
export type { WaterlineDatum } from "./WaterlineChart.js";
export type { ProgressDatum } from "./ProgressChart.js";
export type { HeatmapRow } from "./HeatmapChart.js";
export {
  AreaChart,
  FlameChart,
  GroupedBarChart,
  HeatmapChart,
  LineChart,
  ProgressChart,
  ScatterChart,
  WaterlineChart,
} from "./canonical-wrappers.js";
export type {
  AreaChartProps,
  FlameChartProps,
  GroupedBarChartProps,
  HeatmapChartProps,
  LineChartProps,
  ProgressChartProps,
  ScatterChartProps,
  WaterlineChartProps,
} from "./canonical-wrappers.js";
export {
  BeforeAfterChart,
  MetricBar,
  MirroredAreaChart,
  RankingChart,
  SegmentedChart,
  SparklineChart,
  StatChart,
  TimelineChart,
} from "./canonical-primitives.js";
export type {
  BeforeAfterChartProps,
  BeforeAfterDatum,
  MetricBarDatum,
  MetricBarProps,
  MirroredAreaChartProps,
  RankingChartProps,
  RankingDatum,
  SegmentedChartProps,
  SegmentedDatum,
  SparklineChartProps,
  StatChartProps,
  StatDatum,
  TimelineChartProps,
  TimelineDatum,
} from "./canonical-primitives.js";
export { DigitalNumberChart, PixelNumberChart } from "./DigitalNumberChart.js";
export type {
  DigitalNumberChartProps,
  DigitalNumberDatum,
  PixelNumberChartProps,
  PixelNumberDatum,
} from "./DigitalNumberChart.js";
export { TreeChart } from "./TreeChart.js";
export type { TreeChartProps, TreeNode } from "./TreeChart.js";
