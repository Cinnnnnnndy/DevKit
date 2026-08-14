import { CellLine, clamp, colorProp, finiteNumber, fitChartText } from "./chart-primitives.js";
import { ChartFrame } from "./ChartFrame.js";
import { resolveChartPalette } from "./palette.js";
import type { ChartBaseProps, ChartCell } from "./types.js";

export type HeatmapRow = {
  label: string;
  values: readonly number[];
};

export type HeatmapChartProps = ChartBaseProps & {
  data: readonly HeatmapRow[];
  title?: string;
};

const INTENSITY = ["·", "░", "▒", "▓", "█"] as const;
const ASCII_INTENSITY = [".", ":", "+", "*", "#"] as const;

function intensityCharacter(level: number, unicode: boolean): string {
  return (unicode ? INTENSITY : ASCII_INTENSITY).at(level) ?? " ";
}

function heatCells(
  values: readonly number[],
  columns: number,
  colors: ReturnType<typeof resolveChartPalette>,
  colored: boolean,
  unicode: boolean,
): ChartCell[] {
  return Array.from({ length: columns }, (_, column) => {
    const start = Math.floor((column * values.length) / columns);
    const end = Math.max(start + 1, Math.ceil(((column + 1) * values.length) / columns));
    let value = 0;
    for (let index = start; index < Math.min(end, values.length); index += 1)
      value = Math.max(value, finiteNumber(values[index] ?? 0));
    value = clamp(value, 0, 100);
    const level = clamp(Math.round(value / 25), 0, 4);
    return {
      character: intensityCharacter(level, unicode),
      color: colored ? colors.heatmap.at(level) : undefined,
      background: colored ? colors.heatmap.at(Math.max(0, level - 1)) : undefined,
    };
  });
}

export function HeatmapChart({
  width,
  height,
  data,
  palette,
  capabilities,
  title = "RMA_Die",
}: HeatmapChartProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const colored = capabilities?.colorMode !== "none";
  let longestLabel = 3;
  let sourceColumns = 0;
  for (const row of data) {
    longestLabel = Math.max(longestLabel, row.label.length);
    sourceColumns = Math.max(sourceColumns, row.values.length);
  }
  const labelWidth = clamp(Math.min(8, longestLabel), 3, 8);
  const legendCells: ChartCell[] = colors.heatmap.slice(0, 5).map((color, index) => ({
    character: intensityCharacter(index, capabilities?.unicode !== false),
    color: colored ? color : undefined,
  }));

  return (
    <ChartFrame
      width={width}
      height={height}
      palette={palette}
      capabilities={capabilities}
      title={title}
      legend={[
        { label: "0", marker: "" },
        ...legendCells.map((cell) => ({ label: "", marker: cell.character, color: cell.color })),
        { label: "100", marker: "" },
      ]}
    >
      {(layout) => {
        const localMaxColumns = Math.max(1, layout.width - labelWidth - 1);
        const localColumns = Math.min(localMaxColumns, sourceColumns);
        const rows = data.slice(0, Math.max(0, layout.height - 1));
        return (
          <box width={layout.width} height={layout.height} overflow="hidden" flexDirection="column">
            {rows.map((row, index) => (
              <box key={`${row.label}-${index}`} height={1} flexShrink={0} flexDirection="row">
                <text
                  width={labelWidth + 1}
                  wrapMode="none"
                  {...colorProp("fg", colored ? colors.text : undefined)}
                >
                  {fitChartText(
                    index === 0 || index === rows.length - 1 ? row.label : "",
                    labelWidth,
                  )}{" "}
                </text>
                <CellLine
                  cells={heatCells(
                    row.values,
                    localColumns,
                    colors,
                    colored,
                    capabilities?.unicode !== false,
                  )}
                  defaultColor={colored ? colors.text : undefined}
                />
              </box>
            ))}
            <box height={1} flexDirection="row">
              <text width={labelWidth + 1}> </text>
              <text wrapMode="none" {...colorProp("fg", colored ? colors.border : undefined)}>
                11A 12A 13A 14A 15A 16A 17A
              </text>
            </box>
          </box>
        );
      }}
    </ChartFrame>
  );
}

export default HeatmapChart;
