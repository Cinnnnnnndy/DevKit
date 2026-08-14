import { clamp, colorProp, finiteNumber, fitChartText } from "./chart-primitives.js";
import { resolveChartPalette } from "./palette.js";
import type { ChartBaseProps } from "./types.js";

export type WaterlineDatum = {
  label: string;
  value: number;
  warning?: number;
  critical?: number;
  unit?: string;
};

export type WaterlineChartProps = ChartBaseProps & {
  data: readonly WaterlineDatum[];
};

function WaterlineCard({
  datum,
  width,
  height,
  palette,
  colored,
  fillColor,
  unicode,
}: {
  datum: WaterlineDatum;
  width: number;
  height: number;
  palette: ReturnType<typeof resolveChartPalette>;
  colored: boolean;
  fillColor: string;
  unicode: boolean;
}) {
  const value = clamp(finiteNumber(datum.value), 0, 100);
  const segments = 5;
  const active = clamp(Math.round(value / 20), value > 0 ? 1 : 0, segments);
  const slot = (unicode ? "▪" : "#").repeat(Math.max(1, width - 4));

  return (
    <box
      width={width}
      height={height}
      flexShrink={0}
      border
      {...colorProp("borderColor", colored ? palette.border : undefined)}
      title={fitChartText(datum.label, Math.max(1, width - 4)).trimEnd()}
      {...colorProp("titleColor", colored ? palette.text : undefined)}
      flexDirection="column"
      overflow="hidden"
    >
      <text wrapMode="none" {...colorProp("fg", colored ? palette.text : undefined)}>
        {value}
        {datum.unit ?? "%"}
      </text>
      {Array.from({ length: segments }, (_, row) => {
        const level = segments - row;
        const filled = level <= active;
        return (
          <text
            key={`level-${segments - row}`}
            wrapMode="none"
            {...colorProp("fg", colored && filled ? fillColor : undefined)}
          >
            {filled ? slot : " ".repeat(slot.length)}
          </text>
        );
      })}
    </box>
  );
}

export function WaterlineChart({
  width,
  height,
  data,
  palette,
  capabilities,
}: WaterlineChartProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const colored = capabilities?.colorMode !== "none";
  const visible = data.slice(0, Math.min(data.length, 3));
  const cardWidth = Math.max(1, Math.min(18, Math.floor(width)));
  const cardHeight = 8;
  const gap = 1;
  const vertical = width < visible.length * cardWidth + Math.max(0, visible.length - 1) * gap;
  const fillColors = [colors.red, colors.orange, colors.waterGreen ?? colors.green] as const;

  return (
    <box
      width="100%"
      height={Math.max(1, Math.floor(height))}
      overflow="hidden"
      flexDirection={vertical ? "column" : "row"}
      gap={gap}
    >
      {visible.map((datum, index) => (
        <WaterlineCard
          key={`${datum.label}-${index}`}
          datum={datum}
          width={cardWidth}
          height={cardHeight}
          palette={colors}
          colored={colored}
          fillColor={fillColors[index] ?? colors.green}
          unicode={capabilities?.unicode !== false}
        />
      ))}
    </box>
  );
}

export default WaterlineChart;
