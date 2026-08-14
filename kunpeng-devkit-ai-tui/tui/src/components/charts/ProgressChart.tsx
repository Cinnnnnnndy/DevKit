import { CellLine, clamp, colorProp, finiteNumber, fitChartText } from "./chart-primitives.js";
import { ChartFrame } from "./ChartFrame.js";
import { resolveChartPalette } from "./palette.js";
import type { ChartBaseProps, ChartCell } from "./types.js";

export type ProgressDatum = {
  label: string;
  value: number;
  status?: string;
};

export type ProgressChartProps = ChartBaseProps & {
  data: readonly ProgressDatum[];
  title?: string;
};

function progressCells(
  value: number,
  width: number,
  colors: ReturnType<typeof resolveChartPalette>,
  colored: boolean,
  unicode: boolean,
): ChartCell[] {
  const active = Math.round((clamp(value, 0, 100) / 100) * width);
  return Array.from({ length: width }, (_, index) => {
    if (index >= active)
      return { character: unicode ? "▌" : ".", color: colored ? colors.empty : undefined };
    const greenEnd = Math.min(9, width);
    const yellowEnd = Math.min(16, width);
    return {
      character: unicode ? "▌" : index < greenEnd ? "#" : index < yellowEnd ? "*" : "+",
      color: colored
        ? index < greenEnd
          ? colors.progressGreen
          : index < yellowEnd
            ? colors.yellow
            : colors.red
        : undefined,
    };
  });
}

export function ProgressChart({
  width,
  height,
  data,
  palette,
  capabilities,
  title = "RMA_Die",
}: ProgressChartProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const colored = capabilities?.colorMode !== "none";
  return (
    <ChartFrame
      width={width}
      height={height}
      palette={palette}
      capabilities={capabilities}
      title={title}
    >
      {(layout) => {
        const valueWidth = 8;
        const preferredBarWidth = 36;
        const labelWidth = Math.min(
          12,
          Math.max(6, layout.width - preferredBarWidth - valueWidth - 2),
        );
        const barWidth = Math.max(
          1,
          Math.min(preferredBarWidth, layout.width - labelWidth - valueWidth - 2),
        );
        const visibleRows = data.slice(0, Math.max(0, layout.height));
        return (
          <box width={layout.width} height={layout.height} overflow="hidden" flexDirection="column">
            {visibleRows.map((datum, index) => {
              const value = clamp(finiteNumber(datum.value), 0, 100);
              return (
                <box
                  key={`${datum.label}-${index}`}
                  height={1}
                  flexShrink={0}
                  flexDirection="row"
                  overflow="hidden"
                >
                  <text
                    width={labelWidth}
                    wrapMode="none"
                    {...colorProp("fg", colored ? colors.text : undefined)}
                  >
                    {fitChartText(datum.label, labelWidth)}
                  </text>
                  <text {...colorProp("fg", colored ? colors.border : undefined)}>[</text>
                  <CellLine
                    cells={progressCells(
                      value,
                      barWidth,
                      colors,
                      colored,
                      capabilities?.unicode !== false,
                    )}
                    defaultColor={colored ? colors.text : undefined}
                  />
                  <text {...colorProp("fg", colored ? colors.border : undefined)}>]</text>
                  <text
                    width={valueWidth}
                    wrapMode="none"
                    {...colorProp("fg", colored ? colors.white : undefined)}
                  >{` ${value.toFixed(2)}%`}</text>
                </box>
              );
            })}
          </box>
        );
      }}
    </ChartFrame>
  );
}

export default ProgressChart;
