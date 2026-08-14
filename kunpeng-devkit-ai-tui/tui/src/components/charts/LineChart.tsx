import {
  brailleCharacter,
  capabilityColor,
  CellLine,
  createBraillePixels,
  drawBrailleSegment,
  finiteNumber,
} from "./chart-primitives.js";
import { ChartFrame } from "./ChartFrame.js";
import { resolveChartCapabilities, resolveChartPalette } from "./palette.js";
import type { ChartBaseProps, ChartCell } from "./types.js";

export type LineTone = "green" | "orange";
export type LineSeries = { label: string; tone: LineTone; values: readonly number[] };
export type LineChartProps = ChartBaseProps & { data: readonly LineSeries[] };

function extent(data: readonly LineSeries[]): [number, number] {
  let minimum = Number.POSITIVE_INFINITY;
  let maximum = Number.NEGATIVE_INFINITY;
  for (const series of data)
    for (const value of series.values)
      if (Number.isFinite(value)) {
        minimum = Math.min(minimum, value);
        maximum = Math.max(maximum, value);
      }
  if (!Number.isFinite(minimum) || !Number.isFinite(maximum)) return [0, 1];
  return minimum === maximum ? [minimum - 1, maximum + 1] : [minimum, maximum];
}

/** T2 two-series thin line chart. No fill; green and orange match the source image. */
export function LineChart({
  width,
  height,
  title = "RMA_Die",
  data,
  palette,
  capabilities,
}: LineChartProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const caps = resolveChartCapabilities(capabilities);
  const [minimum, maximum] = extent(data);
  const visibleSeries = data.slice(0, 2);
  return (
    <ChartFrame
      width={width}
      height={height}
      palette={palette}
      capabilities={caps}
      title={title}
      legend={visibleSeries.map((series) => ({
        label: series.label,
        color: colors[series.tone],
        marker: caps.unicode ? "━" : "-",
      }))}
      yAxis={{ minimum: String(Math.round(minimum)), maximum: String(Math.round(maximum)) }}
    >
      {({ width: plotWidth, height: plotHeight }) => {
        const layers = visibleSeries.map(() => createBraillePixels(plotWidth, plotHeight));
        visibleSeries.forEach((series, layerIndex) => {
          const layer = layers.at(layerIndex);
          if (!layer) return;
          const sampleCount = Math.min(series.values.length, Math.max(2, plotWidth * 2));
          const sampled = Array.from(
            { length: sampleCount },
            (_, index) =>
              series.values[
                Math.round((index * (series.values.length - 1)) / Math.max(1, sampleCount - 1))
              ] ?? 0,
          );
          const points = sampled.map((value, index) => ({
            x: Math.round((index / Math.max(1, sampled.length - 1)) * (plotWidth * 2 - 1)),
            y: Math.round(
              ((maximum - finiteNumber(value)) / Math.max(1e-9, maximum - minimum)) *
                (plotHeight * 4 - 1),
            ),
          }));
          for (let index = 1; index < points.length; index += 1) {
            const from = points.at(index - 1);
            const to = points.at(index);
            if (from && to) drawBrailleSegment(layer, from, to);
          }
        });
        const rows: ChartCell[][] = Array.from({ length: plotHeight }, (_, row) =>
          Array.from({ length: plotWidth }, (_, column) => {
            let mask = 0;
            let owner = 0;
            let hits = 0;
            layers.forEach((layer, index) => {
              const next = layer[row]?.[column] ?? 0;
              if (next) {
                mask |= next;
                owner = index;
                hits += 1;
              }
            });
            const series = visibleSeries[owner];
            return {
              character: brailleCharacter(mask, caps.braille && caps.unicode),
              color: mask
                ? capabilityColor(hits > 1 ? colors.white : colors[series?.tone ?? "green"], caps)
                : undefined,
            };
          }),
        );
        return (
          <box flexGrow={1} flexDirection="column" overflow="hidden">
            {rows.map((cells, row) => (
              // biome-ignore lint/suspicious/noArrayIndexKey: Canvas rows are positional, stateless, and never reordered.
              <CellLine key={row} cells={cells} />
            ))}
          </box>
        );
      }}
    </ChartFrame>
  );
}

export default LineChart;
