import {
  capabilityColor,
  CellLine,
  brailleCharacter,
  clamp,
  createBraillePixels,
  finiteNumber,
  setBraillePixel,
} from "./chart-primitives.js";
import { ChartFrame } from "./ChartFrame.js";
import { resolveChartCapabilities, resolveChartPalette } from "./palette.js";
import type { ChartBaseProps, ChartCell } from "./types.js";

export type ScatterTone = "red" | "orange" | "green";
export type ScatterDatum = { x: number; y: number; tone?: ScatterTone; size?: number };
export type ScatterChartProps = ChartBaseProps & { data: readonly ScatterDatum[] };

const SCATTER_TONES = ["red", "orange", "green"] as const;

function scatterExtents(data: readonly ScatterDatum[]): [number, number, number, number] {
  let minimumX = Number.POSITIVE_INFINITY;
  let maximumX = Number.NEGATIVE_INFINITY;
  let minimumY = Number.POSITIVE_INFINITY;
  let maximumY = Number.NEGATIVE_INFINITY;
  for (const point of data) {
    if (Number.isFinite(point.x)) {
      minimumX = Math.min(minimumX, point.x);
      maximumX = Math.max(maximumX, point.x);
    }
    if (Number.isFinite(point.y)) {
      minimumY = Math.min(minimumY, point.y);
      maximumY = Math.max(maximumY, point.y);
    }
  }
  if (!Number.isFinite(minimumX) || !Number.isFinite(maximumX)) {
    minimumX = 0;
    maximumX = 1;
  } else if (minimumX === maximumX) {
    minimumX -= 1;
    maximumX += 1;
  }
  if (!Number.isFinite(minimumY) || !Number.isFinite(maximumY)) {
    minimumY = 0;
    maximumY = 1;
  } else if (minimumY === maximumY) {
    minimumY -= 1;
    maximumY += 1;
  }
  return [minimumX, maximumX, minimumY, maximumY];
}

/** T2 point plot using the source image's red → orange → green tones. Falls back to visible dots. */
export function ScatterChart({
  width,
  height,
  title = "RMA_Die",
  data,
  palette,
  capabilities,
}: ScatterChartProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const caps = resolveChartCapabilities(capabilities);
  const [minimumX, maximumX, minimumY, maximumY] = scatterExtents(data);
  const toneColor = { red: colors.red, orange: colors.orange, green: colors.green } as const;
  return (
    <ChartFrame
      width={width}
      height={height}
      palette={palette}
      capabilities={caps}
      title={title}
      legend={[
        { label: "低", color: colors.red },
        { label: "中", color: colors.orange },
        { label: "高", color: colors.green },
      ]}
      xAxis={{ minimum: String(minimumX), maximum: String(maximumX) }}
      yAxis={{ minimum: String(minimumY), maximum: String(maximumY) }}
    >
      {({ width: plotWidth, height: plotHeight }) => {
        const layers = SCATTER_TONES.map(() => createBraillePixels(plotWidth, plotHeight));
        for (const point of data.slice(0, Math.max(1, plotWidth * plotHeight * 8))) {
          const x = Math.round(
            clamp((finiteNumber(point.x) - minimumX) / Math.max(1e-9, maximumX - minimumX), 0, 1) *
              (plotWidth * 2 - 1),
          );
          const y = Math.round(
            (1 -
              clamp(
                (finiteNumber(point.y) - minimumY) / Math.max(1e-9, maximumY - minimumY),
                0,
                1,
              )) *
              (plotHeight * 4 - 1),
          );
          const layerIndex = SCATTER_TONES.indexOf(point.tone ?? "orange");
          const layer = layers.at(layerIndex);
          if (!layer) continue;
          const radius = clamp(Math.round(finiteNumber(point.size ?? 1, 1)), 1, 3) - 1;
          for (let offsetY = -radius; offsetY <= radius; offsetY += 1)
            for (let offsetX = -radius; offsetX <= radius; offsetX += 1)
              if (offsetX * offsetX + offsetY * offsetY <= radius * radius + 1)
                setBraillePixel(layer, x + offsetX, y + offsetY);
        }
        const rows: ChartCell[][] = Array.from({ length: plotHeight }, (_, row) =>
          Array.from({ length: plotWidth }, (_, column) => {
            let mask = 0;
            let tone: ScatterTone = "orange";
            let hits = 0;
            layers.forEach((layer, index) => {
              const next = layer[row]?.[column] ?? 0;
              if (next) {
                mask |= next;
                tone = SCATTER_TONES.at(index) ?? "orange";
                hits += 1;
              }
            });
            return {
              character: brailleCharacter(mask, caps.braille && caps.unicode),
              color: mask
                ? capabilityColor(hits > 1 ? colors.white : toneColor[tone], caps)
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

export default ScatterChart;
