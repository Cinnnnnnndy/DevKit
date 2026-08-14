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

export type DivergingBarChartDatum = { label: string; positive: number; negative: number };
export type DivergingBarChartProps = ChartBaseProps & { data: readonly DivergingBarChartDatum[] };

/** T1 zero-axis chart: blue grows upward, green grows downward. */
export function DivergingBarChart({
  width,
  height,
  title = "RMA_Die",
  data,
  palette,
  capabilities,
}: DivergingBarChartProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const caps = resolveChartCapabilities(capabilities);
  let maximum = 1;
  for (const item of data)
    maximum = Math.max(
      maximum,
      Math.abs(finiteNumber(item.positive)),
      Math.abs(finiteNumber(item.negative)),
    );
  return (
    <ChartFrame
      width={width}
      height={height}
      palette={palette}
      capabilities={caps}
      title={title}
      legend={[
        { label: "正值", color: colors.blue, marker: "▲" },
        { label: "负值", color: colors.green, marker: "▼" },
      ]}
      yAxis={{
        minimum: `-${Math.round(maximum)}`,
        midpoint: "0",
        maximum: String(Math.round(maximum)),
      }}
    >
      {({ width: plotWidth, height: plotHeight }) => {
        const groupWidth = 3;
        const visible = data.slice(0, Math.max(1, Math.floor(plotWidth / groupWidth)));
        const labels = plotHeight >= 4 ? 1 : 0;
        const drawable = Math.max(3, plotHeight - labels);
        const topHeight = Math.max(1, Math.floor((drawable - 1) / 2));
        const bottomHeight = Math.max(1, drawable - topHeight - 1);
        const rows = (() => {
          const output: ChartCell[][] = [];
          for (let row = 0; row < topHeight; row += 1) {
            const threshold = ((topHeight - row) / topHeight) * maximum;
            output.push(
              visible.flatMap((item) => [
                {
                  character:
                    finiteNumber(item.positive) >= threshold ? (caps.unicode ? "█" : "#") : " ",
                  color: capabilityColor(colors.blue, caps),
                },
                { character: " " },
                { character: " " },
              ]),
            );
          }
          output.push(
            Array.from({ length: Math.min(plotWidth, visible.length * groupWidth) }, () => ({
              character: caps.unicode ? "─" : "-",
              color: capabilityColor(colors.border, caps),
            })),
          );
          for (let row = 0; row < bottomHeight; row += 1) {
            const threshold = ((row + 1) / bottomHeight) * maximum;
            output.push(
              visible.flatMap((item) => [
                {
                  character:
                    Math.abs(finiteNumber(item.negative)) >= threshold
                      ? caps.unicode
                        ? "█"
                        : "#"
                      : " ",
                  color: capabilityColor(colors.green, caps),
                },
                { character: " " },
                { character: " " },
              ]),
            );
          }
          return output;
        })();
        return (
          <box flexGrow={1} flexDirection="column" overflow="hidden">
            {rows.map((cells, row) => (
              // biome-ignore lint/suspicious/noArrayIndexKey: Canvas rows are positional, stateless, and never reordered.
              <CellLine key={row} cells={cells} />
            ))}
            {labels ? (
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

export default DivergingBarChart;
