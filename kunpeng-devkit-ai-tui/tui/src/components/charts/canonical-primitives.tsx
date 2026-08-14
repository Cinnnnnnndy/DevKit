import { clamp, colorProp, finiteNumber, fitChartText } from "./chart-primitives.js";
import { fitPrimitive, type PrimitiveId, PRIMITIVE_SPECS } from "./primitive-layout.js";
import { resolveChartCapabilities, resolveChartPalette } from "./palette.js";
import type { ChartBaseProps } from "./types.js";

function FitBox({
  id,
  width,
  height,
  children,
}: {
  id: PrimitiveId;
  width: number;
  height: number;
  children: (width: number, height: number) => React.ReactNode;
}) {
  const fit = fitPrimitive(id, width, height);
  if (!fit.fits)
    return (
      <box width={Math.max(1, width)} height={Math.max(1, height)} overflow="hidden">
        <text wrapMode="none" truncate>
          {fit.fallback?.description ?? "chart unavailable"}
        </text>
      </box>
    );
  return <>{children(fit.box.width, fit.box.height)}</>;
}

export type MetricBarDatum = { label: string; value: number; maximum?: number; unit?: string };
export type MetricBarProps = ChartBaseProps & { data: readonly MetricBarDatum[] };

/** 横向指标条使用八分之一方块精度和共享数据刻度。 */
export function MetricBar({ width, height, data, palette, capabilities }: MetricBarProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const caps = resolveChartCapabilities(capabilities);
  const scale = Math.max(
    1,
    ...data.map((datum) =>
      Math.max(finiteNumber(datum.maximum ?? datum.value), finiteNumber(datum.value)),
    ),
  );
  return (
    <FitBox id="metric-bar" width={width} height={height}>
      {(fitWidth, fitHeight) => {
        const labelWidth = Math.min(12, Math.max(4, Math.floor(fitWidth * 0.3)));
        const valueWidth = Math.min(
          8,
          Math.max(
            4,
            ...data.map((datum) => `${finiteNumber(datum.value)}${datum.unit ?? ""}`.length),
          ),
        );
        const barWidth = Math.max(1, fitWidth - labelWidth - valueWidth - 2);
        const fractions = ["", "▏", "▎", "▍", "▌", "▋", "▊", "▉"];
        const visible = data.slice(0, fitHeight);
        const hidden = Math.max(0, data.length - visible.length);
        return (
          <box width={fitWidth} height={fitHeight} flexDirection="column" overflow="hidden">
            {visible.map((datum, index) => {
              const value = Math.max(0, finiteNumber(datum.value));
              const eighths = Math.round((value / scale) * barWidth * 8);
              const full = Math.floor(eighths / 8);
              const partial = fractions[eighths % 8] ?? "";
              const bar = `${"█".repeat(full)}${partial}`;
              return (
                <text
                  key={`${datum.label}-${index}`}
                  wrapMode="none"
                  truncate
                  {...colorProp("fg", caps.colorMode === "none" ? undefined : colors.orange)}
                >
                  <span {...colorProp("fg", caps.colorMode === "none" ? undefined : colors.text)}>
                    {fitChartText(datum.label, labelWidth)}{" "}
                  </span>
                  {fitChartText(bar, barWidth)}{" "}
                  <span {...colorProp("fg", caps.colorMode === "none" ? undefined : colors.white)}>
                    {fitChartText(`${value}${datum.unit ?? ""}`, valueWidth)}
                  </span>
                </text>
              );
            })}
            {hidden > 0 && fitHeight > 0 ? (
              <text wrapMode="none" truncate>
                … {hidden} more
              </text>
            ) : null}
          </box>
        );
      }}
    </FitBox>
  );
}

export type RankingDatum = { label: string; value: number; unit?: string };
export type RankingChartProps = ChartBaseProps & { data: readonly RankingDatum[] };
export function RankingChart(props: RankingChartProps) {
  const sorted = [...props.data].sort((a, b) => finiteNumber(b.value) - finiteNumber(a.value));
  return <MetricBar {...props} data={sorted} />;
}

export type BeforeAfterDatum = { label: string; before: number; after: number; unit?: string };
export type BeforeAfterChartProps = ChartBaseProps & { data: readonly BeforeAfterDatum[] };
export function BeforeAfterChart({
  width,
  height,
  data,
  palette,
  capabilities,
}: BeforeAfterChartProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const colored = capabilities?.colorMode !== "none";
  return (
    <FitBox id="before-after" width={width} height={height}>
      {(fitWidth, fitHeight) => (
        <box width={fitWidth} height={fitHeight} flexDirection="column" overflow="hidden">
          {data.slice(0, fitHeight).map((datum, index) => {
            const before = finiteNumber(datum.before);
            const after = finiteNumber(datum.after);
            const delta = before === 0 ? 0 : ((after - before) / Math.abs(before)) * 100;
            return (
              <text key={`${datum.label}-${index}`} wrapMode="none" truncate>
                {datum.label}{" "}
                <span {...colorProp("fg", colored ? colors.red : undefined)}>
                  {before}
                  {datum.unit ?? ""}
                </span>{" "}
                →{" "}
                <span {...colorProp("fg", colored ? colors.green : undefined)}>
                  {after}
                  {datum.unit ?? ""}
                </span>{" "}
                <span
                  {...colorProp(
                    "fg",
                    colored ? (delta <= 0 ? colors.green : colors.red) : undefined,
                  )}
                >
                  {delta >= 0 ? "+" : ""}
                  {delta.toFixed(0)}%
                </span>
              </text>
            );
          })}
        </box>
      )}
    </FitBox>
  );
}

export type SparklineChartProps = ChartBaseProps & {
  data: readonly number[];
  label?: string;
  unit?: string;
};
export function SparklineChart({
  width,
  height,
  data,
  label = "trend",
  unit = "",
  palette,
  capabilities,
}: SparklineChartProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const colored = capabilities?.colorMode !== "none";
  return (
    <FitBox id="sparkline" width={width} height={height}>
      {(fitWidth) => {
        const blocks = capabilities?.unicode === false ? ".:-=+*#@" : "▁▂▃▄▅▆▇█";
        const safe = data.map((value) => finiteNumber(value));
        const min = Math.min(0, ...safe);
        const max = Math.max(1, ...safe);
        const available = Math.max(1, fitWidth - label.length - unit.length - 8);
        const samples = Array.from(
          { length: Math.min(available, safe.length) },
          (_, index) =>
            safe[
              Math.floor((index * safe.length) / Math.max(1, Math.min(available, safe.length)))
            ] ?? 0,
        );
        const spark = samples
          .map((value) => blocks[Math.round(((value - min) / Math.max(1, max - min)) * 7)] ?? " ")
          .join("");
        return (
          <text width={fitWidth} wrapMode="none" truncate>
            {label} <span {...colorProp("fg", colored ? colors.blue : undefined)}>{spark}</span>{" "}
            {safe.at(-1) ?? 0}
            {unit}
          </text>
        );
      }}
    </FitBox>
  );
}

export type MirroredAreaChartProps = ChartBaseProps & {
  up: readonly number[];
  down: readonly number[];
  labels?: readonly [string, string];
};
export function MirroredAreaChart({
  width,
  height,
  up,
  down,
  labels = ["up", "down"],
  palette,
  capabilities,
}: MirroredAreaChartProps) {
  return (
    <FitBox id="mirrored-area" width={width} height={height}>
      {(fitWidth, fitHeight) => (
        <box width={fitWidth} height={fitHeight} flexDirection="column" overflow="hidden">
          <SparklineChart
            width={fitWidth}
            height={1}
            data={up}
            label={`↑ ${labels[0]}`}
            palette={palette}
            capabilities={capabilities}
          />
          <SparklineChart
            width={fitWidth}
            height={1}
            data={down}
            label={`↓ ${labels[1]}`}
            palette={palette}
            capabilities={capabilities}
          />
        </box>
      )}
    </FitBox>
  );
}

export type TimelineDatum = { label: string; start: number; end: number; status?: string };
export type TimelineChartProps = ChartBaseProps & { data: readonly TimelineDatum[] };
export function TimelineChart({ width, height, data, palette, capabilities }: TimelineChartProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const colored = capabilities?.colorMode !== "none";
  const maximum = Math.max(1, ...data.map((item) => finiteNumber(item.end)));
  return (
    <FitBox id="timeline" width={width} height={height}>
      {(fitWidth, fitHeight) => (
        <box width={fitWidth} height={fitHeight} flexDirection="column" overflow="hidden">
          {data.slice(0, fitHeight).map((item, index) => {
            const labelWidth = Math.min(14, Math.max(5, Math.floor(fitWidth * 0.25)));
            const laneWidth = Math.max(1, fitWidth - labelWidth - 8);
            const start = clamp(Math.round((item.start / maximum) * laneWidth), 0, laneWidth);
            const end = clamp(Math.round((item.end / maximum) * laneWidth), start + 1, laneWidth);
            return (
              <text key={`${item.label}-${index}`} wrapMode="none" truncate>
                <span {...colorProp("fg", colored ? colors.text : undefined)}>
                  {fitChartText(item.label, labelWidth)}
                </span>
                {" ".repeat(start)}
                <span {...colorProp("fg", colored ? colors.cyan : undefined)}>
                  {"━".repeat(Math.max(1, end - start))}
                </span>{" "}
                {item.end - item.start}ms
              </text>
            );
          })}
        </box>
      )}
    </FitBox>
  );
}

export type SegmentedDatum = { label: string; value: number };
export type SegmentedChartProps = ChartBaseProps & { data: readonly SegmentedDatum[] };
export function SegmentedChart({
  width,
  height,
  data,
  palette,
  capabilities,
}: SegmentedChartProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const colored = capabilities?.colorMode !== "none";
  const total = Math.max(
    1,
    data.reduce((sum, item) => sum + Math.max(0, finiteNumber(item.value)), 0),
  );
  return (
    <FitBox id="segmented" width={width} height={height}>
      {(fitWidth) => {
        const barWidth = Math.max(1, fitWidth - 2);
        const tones = [colors.green, colors.orange, colors.cyan, colors.blue];
        return (
          <box width={fitWidth} height={2} flexDirection="column" overflow="hidden">
            <text wrapMode="none">
              {data.map((item, index) => (
                <span
                  key={`${item.label}-${index}`}
                  {...colorProp("fg", colored ? tones[index % tones.length] : undefined)}
                >
                  {"█".repeat(Math.max(1, Math.round((item.value / total) * barWidth)))}
                </span>
              ))}
            </text>
            <text wrapMode="none" truncate>
              {data.map((item) => `${item.label} ${item.value}`).join(" · ")}
            </text>
          </box>
        );
      }}
    </FitBox>
  );
}

export type StatDatum = { label: string; value: string | number; detail?: string };
export type StatChartProps = ChartBaseProps & { data: readonly StatDatum[] };
export function StatChart({ width, height, data, palette, capabilities }: StatChartProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const colored = capabilities?.colorMode !== "none";
  return (
    <FitBox id="stat" width={width} height={height}>
      {(fitWidth, fitHeight) => (
        <box width={fitWidth} height={fitHeight} flexDirection="column" overflow="hidden">
          {data.slice(0, fitHeight).map((item, index) => (
            <text key={`${item.label}-${index}`} wrapMode="none" truncate>
              <span {...colorProp("fg", colored ? colors.text : undefined)}>{item.label}</span>{" "}
              <span {...colorProp("fg", colored ? colors.white : undefined)}>{item.value}</span>
              {item.detail ? ` · ${item.detail}` : ""}
            </text>
          ))}
        </box>
      )}
    </FitBox>
  );
}

export function primitiveFallbackLabel(id: PrimitiveId): string {
  return PRIMITIVE_SPECS[id].fallback.description;
}
