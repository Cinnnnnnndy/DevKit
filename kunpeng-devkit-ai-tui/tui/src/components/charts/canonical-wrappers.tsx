import { AreaChart as LegacyAreaChart, type AreaChartProps } from "./AreaChart.js";
import { FlameChart as LegacyFlameChart, type FlameChartProps } from "./FlameChart.js";
import {
  GroupedBarChart as LegacyGroupedBarChart,
  type GroupedBarChartProps,
} from "./GroupedBarChart.js";
import { HeatmapChart as LegacyHeatmapChart, type HeatmapChartProps } from "./HeatmapChart.js";
import { LineChart as LegacyLineChart, type LineChartProps } from "./LineChart.js";
import { fitPrimitive, type PrimitiveId } from "./primitive-layout.js";
import { ProgressChart as LegacyProgressChart, type ProgressChartProps } from "./ProgressChart.js";
import { ScatterChart as LegacyScatterChart, type ScatterChartProps } from "./ScatterChart.js";
import {
  WaterlineChart as LegacyWaterlineChart,
  type WaterlineChartProps,
} from "./WaterlineChart.js";

function Fallback({ id, width, height }: { id: PrimitiveId; width: number; height: number }) {
  const fit = fitPrimitive(id, width, height);
  return (
    <box width={Math.max(1, width)} height={Math.max(1, height)} overflow="hidden">
      <text wrapMode="none" truncate>
        {fit.fallback?.description}
      </text>
    </box>
  );
}

export function GroupedBarChart(props: GroupedBarChartProps) {
  const fit = fitPrimitive("grouped-bar", props.width, props.height);
  return fit.fits ? (
    <LegacyGroupedBarChart {...props} width={fit.box.width} height={fit.box.height} />
  ) : (
    <Fallback id="grouped-bar" width={props.width} height={props.height} />
  );
}
export function LineChart(props: LineChartProps) {
  const fit = fitPrimitive("line", props.width, props.height);
  return fit.fits ? (
    <LegacyLineChart {...props} width={fit.box.width} height={fit.box.height} />
  ) : (
    <Fallback id="line" width={props.width} height={props.height} />
  );
}
export function AreaChart(props: AreaChartProps) {
  const fit = fitPrimitive("area", props.width, props.height);
  return fit.fits ? (
    <LegacyAreaChart {...props} width={fit.box.width} height={fit.box.height} />
  ) : (
    <Fallback id="area" width={props.width} height={props.height} />
  );
}
export function ScatterChart(props: ScatterChartProps) {
  const fit = fitPrimitive("scatter", props.width, props.height);
  return fit.fits ? (
    <LegacyScatterChart {...props} width={fit.box.width} height={fit.box.height} />
  ) : (
    <Fallback id="scatter" width={props.width} height={props.height} />
  );
}
export function FlameChart(props: FlameChartProps) {
  const fit = fitPrimitive("flame", props.width, props.height);
  return fit.fits ? (
    <LegacyFlameChart {...props} width={fit.box.width} height={fit.box.height} />
  ) : (
    <Fallback id="flame" width={props.width} height={props.height} />
  );
}
export function WaterlineChart(props: WaterlineChartProps) {
  const fit = fitPrimitive("waterline", props.width, props.height);
  return fit.fits ? (
    <LegacyWaterlineChart {...props} width={fit.box.width} height={fit.box.height} />
  ) : (
    <Fallback id="waterline" width={props.width} height={props.height} />
  );
}
export function ProgressChart(props: ProgressChartProps) {
  const fit = fitPrimitive("progress", props.width, props.height);
  return fit.fits ? (
    <LegacyProgressChart {...props} width={fit.box.width} height={fit.box.height} />
  ) : (
    <Fallback id="progress" width={props.width} height={props.height} />
  );
}
export function HeatmapChart(props: HeatmapChartProps) {
  const fit = fitPrimitive("heatmap", props.width, props.height);
  return fit.fits ? (
    <LegacyHeatmapChart {...props} width={fit.box.width} height={fit.box.height} />
  ) : (
    <Fallback id="heatmap" width={props.width} height={props.height} />
  );
}

export type {
  AreaChartProps,
  FlameChartProps,
  GroupedBarChartProps,
  HeatmapChartProps,
  LineChartProps,
  ProgressChartProps,
  ScatterChartProps,
  WaterlineChartProps,
};
