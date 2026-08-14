import {
  brailleCharacter,
  CellLine,
  colorProp,
  finiteNumber,
  setBraillePixel,
} from "./chart-primitives.js";
import { ChartFrame } from "./ChartFrame.js";
import { resolveChartCapabilities, resolveChartPalette } from "./palette.js";
import type { ChartBaseProps, ChartCell } from "./types.js";

export type AreaDatum = {
  label: string;
  value: number;
};

export type AreaChartProps = ChartBaseProps & {
  data: readonly AreaDatum[];
  title?: string;
};

function sampleArea(data: readonly AreaDatum[], width: number): number[] {
  if (width <= 0) return [];
  if (data.length === 0) return Array.from({ length: width }, () => 0);
  if (data.length === 1)
    return Array.from({ length: width }, () => clampPercent(data[0]?.value ?? 0));
  if (data.length <= width) {
    return Array.from({ length: width }, (_, column) => {
      const source = (column * (data.length - 1)) / Math.max(1, width - 1);
      const left = Math.floor(source);
      const right = Math.min(data.length - 1, left + 1);
      const leftValue = clampPercent(data[left]?.value ?? 0);
      const rightValue = clampPercent(data[right]?.value ?? 0);
      return leftValue + (rightValue - leftValue) * (source - left);
    });
  }
  const buckets = Array.from({ length: width }, (_, column) => {
    const start = Math.floor((column * data.length) / width);
    const end = Math.max(start + 1, Math.ceil(((column + 1) * data.length) / width));
    let minimum = 100;
    let maximum = 0;
    for (let index = start; index < Math.min(end, data.length); index += 1) {
      const value = clampPercent(data[index]?.value ?? 0);
      minimum = Math.min(minimum, value);
      maximum = Math.max(maximum, value);
    }
    const representativeIndex = Math.min(data.length - 1, Math.floor((start + end - 1) / 2));
    return {
      start,
      end: Math.min(end, data.length),
      minimum,
      maximum,
      representative: clampPercent(data[representativeIndex]?.value ?? 0),
    };
  });
  const sampled: number[] = [];
  buckets.forEach((bucket, column) => {
    const spread = bucket.maximum - bucket.minimum;
    const previousBucket = buckets.at(column - 1);
    const nextBucket = buckets.at(column + 1);
    const previousSpread =
      column > 0 && previousBucket ? previousBucket.maximum - previousBucket.minimum : 0;
    const nextSpread = nextBucket ? nextBucket.maximum - nextBucket.minimum : 0;
    const isolatedPeak =
      spread >= 25 && bucket.maximum >= 75 && previousSpread < 20 && nextSpread < 20;
    if (isolatedPeak || spread < 20) {
      sampled.push(bucket.maximum);
      return;
    }

    let representative = bucket.representative;
    const previous = sampled.at(-1);
    if (previous !== undefined && Math.abs(representative - previous) < 20) {
      const center = Math.floor((bucket.start + bucket.end - 1) / 2);
      for (let offset = 0; offset < bucket.end - bucket.start; offset += 1) {
        const candidates = offset === 0 ? [center] : [center - offset, center + offset];
        const candidateIndex = candidates.find(
          (index) =>
            index >= bucket.start &&
            index < bucket.end &&
            Math.abs(clampPercent(data[index]?.value ?? 0) - previous) >= 20,
        );
        if (candidateIndex !== undefined) {
          representative = clampPercent(data[candidateIndex]?.value ?? 0);
          break;
        }
      }
    }
    sampled.push(representative);
  });
  return sampled;
}

function clampPercent(value: number): number {
  return Math.max(0, Math.min(100, finiteNumber(value)));
}

function timeAxis(width: number): string {
  if (width <= 0) return "";
  const allTicks = ["08:00", "10:00", "12:00", "14:00", "16:00", "18:00", "20:00"];
  const ticks =
    width >= 47
      ? allTicks
      : width >= 26
        ? allTicks.filter((_, index) => index % 2 === 0)
        : ["08:00", "20:00"];
  const cells = Array.from({ length: width }, () => " ");
  ticks.forEach((label, index) => {
    const center = Math.round((index * (width - 1)) / Math.max(1, ticks.length - 1));
    const start = Math.max(
      0,
      Math.min(width - label.length, center - Math.floor(label.length / 2)),
    );
    for (let offset = 0; offset < label.length && start + offset < width; offset += 1)
      cells[start + offset] = label.charAt(offset);
  });
  return cells.join("");
}

export function AreaChart({
  width,
  height,
  data,
  palette,
  capabilities,
  title = "RMA_Die",
}: AreaChartProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const caps = resolveChartCapabilities(capabilities);
  const colored = caps.colorMode !== "none";
  return (
    <ChartFrame
      width={width}
      height={height}
      palette={palette}
      capabilities={caps}
      title={title}
      frameStyle="open"
      yAxis={{ minimum: "0", midpoint: "50", maximum: "100" }}
    >
      {(layout) => {
        const plotHeight = Math.max(1, layout.height - 1);
        const useBraille = caps.braille && caps.unicode;
        const pixelHeight = plotHeight * (useBraille ? 4 : 2);
        const sampleWidth = layout.width * (useBraille ? 2 : 1);
        const values = sampleArea(data, sampleWidth);
        const cells: ChartCell[][] = useBraille
          ? (() => {
              const pixels = Array.from({ length: plotHeight }, () =>
                Array.from({ length: layout.width }, () => 0),
              );
              const peakCells = new Set<string>();
              values.forEach((value, x) => {
                const filledPixels = Math.round((clampPercent(value) / 100) * pixelHeight);
                const boundary = Math.max(0, pixelHeight - filledPixels);
                for (let y = boundary; y < pixelHeight; y += 1) setBraillePixel(pixels, x, y);
                if (value >= 85 && filledPixels > 0)
                  peakCells.add(`${Math.floor(x / 2)}:${Math.floor(boundary / 4)}`);
              });
              return pixels.map((row, y) =>
                row.map((mask, x) => ({
                  character: brailleCharacter(mask, true),
                  color: colored
                    ? peakCells.has(`${x}:${y}`)
                      ? colors.orange
                      : colors.white
                    : undefined,
                })),
              );
            })()
          : Array.from({ length: plotHeight }, (_, row) => {
              const topPixel = row * 2;
              const bottomPixel = topPixel + 1;
              return values.map((value) => {
                const filledPixels = Math.round((clampPercent(value) / 100) * pixelHeight);
                const boundary = pixelHeight - filledPixels;
                const topFilled = topPixel >= boundary;
                const bottomFilled = bottomPixel >= boundary;
                const character =
                  topFilled && bottomFilled
                    ? caps.unicode
                      ? "█"
                      : "#"
                    : bottomFilled
                      ? caps.unicode
                        ? "▄"
                        : "."
                      : " ";
                const peakTip = value >= 85 && bottomFilled && topPixel <= boundary;
                return {
                  character,
                  color: colored ? (peakTip ? colors.orange : colors.white) : undefined,
                };
              });
            });
        return (
          <box width={layout.width} height={layout.height} overflow="hidden" flexDirection="column">
            {cells.map((row, index) => (
              // biome-ignore lint/suspicious/noArrayIndexKey: Canvas rows are positional, stateless, and never reordered.
              <CellLine key={index} cells={row} defaultColor={colored ? colors.text : undefined} />
            ))}
            <text wrapMode="none" {...colorProp("fg", colored ? colors.border : undefined)}>
              {timeAxis(layout.width)}
            </text>
          </box>
        );
      }}
    </ChartFrame>
  );
}

export default AreaChart;
