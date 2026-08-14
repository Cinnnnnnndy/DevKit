import {
  capabilityColor,
  CellLine,
  colorProp,
  finiteNumber,
  fitChartText,
} from "./chart-primitives.js";
import { ChartFrame } from "./ChartFrame.js";
import { resolveChartCapabilities, resolveChartPalette } from "./palette.js";
import type { ChartBaseProps, ChartCell } from "./types.js";

export type BarChartDatum = { label: string; value: number };
export type BarChartProps = ChartBaseProps & { data: readonly BarChartDatum[] };

function sampleBars(data: readonly BarChartDatum[], limit: number): readonly BarChartDatum[] {
  const safeLimit = Math.max(0, Math.floor(limit));
  if (safeLimit === 0) return [];
  if (data.length <= safeLimit) return data;
  const sampled: BarChartDatum[] = [];
  for (let index = 0; index < safeLimit; index += 1) {
    const sourceIndex = Math.round((index * (data.length - 1)) / Math.max(1, safeLimit - 1));
    const item = data.at(sourceIndex);
    if (item) sampled.push(item);
  }
  return sampled;
}

/** T1 single-series vertical bar. ASCII fallback uses # and never depends on color alone. */
export function BarChart({
  width,
  height,
  title = "RMA_Die",
  data,
  palette,
  capabilities,
}: BarChartProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const caps = resolveChartCapabilities(capabilities);
  let maximum = 1;
  for (const item of data) maximum = Math.max(maximum, Math.max(0, finiteNumber(item.value)));
  return (
    <ChartFrame
      width={width}
      height={height}
      palette={palette}
      capabilities={caps}
      title={title}
      yAxis={{
        minimum: "0",
        midpoint: String(Math.round(maximum / 2)),
        maximum: String(Math.round(maximum)),
      }}
    >
      {({ width: plotWidth, height: plotHeight }) => {
        const labelRows = plotHeight >= 3 ? 1 : 0;
        const barHeight = Math.max(1, plotHeight - labelRows);
        const groupWidth = plotWidth >= 24 ? 3 : 2;
        const visible = sampleBars(data, Math.max(1, Math.floor(plotWidth / groupWidth)));
        const rows = Array.from({ length: barHeight }, (_, row): ChartCell[] => {
          const threshold = ((barHeight - row) / barHeight) * maximum;
          return visible.flatMap((item) => {
            const on = Math.max(0, finiteNumber(item.value)) >= threshold;
            return [
              {
                character: on ? (caps.unicode ? "█" : "#") : " ",
                color: on ? capabilityColor(colors.blue, caps) : undefined,
              },
              ...Array.from({ length: groupWidth - 1 }, () => ({ character: " " })),
            ];
          });
        });
        return (
          <box flexGrow={1} flexDirection="column" justifyContent="flex-end" overflow="hidden">
            {rows.map((cells, row) => (
              // biome-ignore lint/suspicious/noArrayIndexKey: Canvas rows are positional, stateless, and never reordered.
              <CellLine key={row} cells={cells} />
            ))}
            {labelRows ? (
              <text wrapMode="none" {...colorProp("fg", capabilityColor(colors.text, caps))}>
                {visible.map((item) => fitChartText(item.label, groupWidth)).join("")}
              </text>
            ) : null}
          </box>
        );
      }}
    </ChartFrame>
  );
}

export default BarChart;
