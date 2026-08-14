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

export type GroupedBarChartDatum = { label: string; values: readonly [number, number, number] };
export type GroupedBarChartProps = ChartBaseProps & { data: readonly GroupedBarChartDatum[] };

/** T1 three-series vertical bar in the source image's blue / green / cyan order. */
export function GroupedBarChart({
  width,
  height,
  title = "RMA_Die",
  data,
  palette,
  capabilities,
}: GroupedBarChartProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const caps = resolveChartCapabilities(capabilities);
  const seriesColors = [colors.blue, colors.green, colors.cyan] as const;
  let maximum = 1;
  for (const item of data)
    for (const value of item.values) maximum = Math.max(maximum, Math.max(0, finiteNumber(value)));
  if (height <= 4) {
    const groupWidth = 4;
    const visible = data.slice(0, Math.max(1, Math.floor(width / groupWidth)));
    const barHeight = Math.max(1, height - 2);
    const rows = Array.from({ length: barHeight }, (_, row): ChartCell[] => {
      const threshold = ((barHeight - row) / barHeight) * maximum;
      return visible.flatMap((item) => [
        ...item.values.map((value, series) => {
          const on = Math.max(0, finiteNumber(value)) >= threshold;
          return {
            character: on ? (caps.unicode ? "█" : "#") : " ",
            color: on ? capabilityColor(seriesColors.at(series) ?? colors.blue, caps) : undefined,
          };
        }),
        { character: " " },
      ]);
    });
    return (
      <box width={width} height={height} flexDirection="column" overflow="hidden">
        <text wrapMode="none" truncate>
          {seriesColors.map((color, index) => (
            <span key={color} {...colorProp("fg", capabilityColor(color, caps))}>
              {caps.unicode ? "■" : "#"}
              {index + 1}
              {index < 2 ? " " : ""}
            </span>
          ))}
        </text>
        {rows.map((cells, row) => (
          // biome-ignore lint/suspicious/noArrayIndexKey: Canvas rows are positional and stable.
          <CellLine key={row} cells={cells} />
        ))}
        <text wrapMode="none" truncate {...colorProp("fg", capabilityColor(colors.text, caps))}>
          {visible.map((item) => fitChartText(item.label, groupWidth)).join("")}
        </text>
      </box>
    );
  }
  return (
    <ChartFrame
      width={width}
      height={height}
      palette={palette}
      capabilities={caps}
      title={title}
      legend={[
        { label: "系列 1", color: colors.blue },
        { label: "系列 2", color: colors.green },
        { label: "系列 3", color: colors.cyan },
      ]}
      yAxis={{
        minimum: "0",
        midpoint: String(Math.round(maximum / 2)),
        maximum: String(Math.round(maximum)),
      }}
    >
      {({ width: plotWidth, height: plotHeight }) => {
        const groupWidth = 4;
        const visible = data.slice(0, Math.max(1, Math.floor(plotWidth / groupWidth)));
        const labelRows = plotHeight >= 3 ? 1 : 0;
        const barHeight = Math.max(1, plotHeight - labelRows);
        const rows = Array.from({ length: barHeight }, (_, row): ChartCell[] => {
          const threshold = ((barHeight - row) / barHeight) * maximum;
          return visible.flatMap((item) => [
            ...item.values.map((value, series) => {
              const on = Math.max(0, finiteNumber(value)) >= threshold;
              return {
                character: on ? (caps.unicode ? "█" : "#") : " ",
                color: on
                  ? capabilityColor(seriesColors.at(series) ?? colors.blue, caps)
                  : undefined,
              };
            }),
            { character: " " },
          ]);
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

export default GroupedBarChart;
