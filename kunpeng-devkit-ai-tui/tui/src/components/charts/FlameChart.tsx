import { capabilityColor, CellLine } from "./chart-primitives.js";
import { ChartFrame } from "./ChartFrame.js";
import { resolveChartCapabilities, resolveChartPalette } from "./palette.js";
import type { ChartBaseProps, ChartCell } from "./types.js";

export type FlameTone = "red" | "green" | "cyan" | "orange";
export type FlameSpan = { label: string; start: number; end: number; tone: FlameTone };
export type FlameChartProps = ChartBaseProps & {
  data: readonly (readonly FlameSpan[])[];
  legend?: readonly [string, string, string, string];
};

const DEFAULT_FLAME_LEGEND = ["Legend1", "Legend2", "Legend2", "Legend2"] as const;
const FLAME_TONES = ["red", "green", "cyan", "orange"] as const;
const NO_COLOR_FILL: Readonly<Record<FlameTone, string>> = {
  red: "█",
  green: "▓",
  cyan: "▒",
  orange: "░",
};

export function aggregateFlameSpans(level: readonly FlameSpan[], width: number): FlameSpan[] {
  const limit = Math.max(1, width * 8);
  const sampled =
    level.length <= limit
      ? level
      : (() => {
          const result: FlameSpan[] = [];
          for (let index = 0; index < limit; index += 1) {
            const sourceIndex = Math.round((index * (level.length - 1)) / Math.max(1, limit - 1));
            const span = level.at(sourceIndex);
            if (span) result.push(span);
          }
          return result;
        })();
  const ordered = [...sampled].sort((left, right) => left.start - right.start);
  const output: FlameSpan[] = [];
  let pending: FlameSpan[] = [];
  const flush = () => {
    if (!pending.length) return;
    const first = pending.at(0);
    const last = pending.at(-1);
    if (!first || !last) {
      pending = [];
      return;
    }
    output.push({
      label: `other×${pending.length}`,
      start: first.start,
      end: last.end,
      tone: "orange",
    });
    pending = [];
  };
  for (const span of ordered) {
    const narrow = ((span.end - span.start) / 100) * width < 2;
    if (!narrow) {
      flush();
      output.push(span);
      continue;
    }
    const previous = pending.at(-1);
    const gapColumns = previous ? ((span.start - previous.end) / 100) * width : 0;
    if (previous && gapColumns >= 1) flush();
    pending.push(span);
  }
  flush();
  return output;
}

function fillLevels(
  data: readonly (readonly FlameSpan[])[],
  height: number,
): readonly (readonly FlameSpan[])[] {
  if (!data.length || height <= 0) return [];
  if (data.length <= height) return data;
  const levels: Array<readonly FlameSpan[]> = [];
  for (let row = 0; row < height; row += 1) {
    const level = data.at(Math.floor((row * data.length) / height));
    if (level) levels.push(level);
  }
  return levels;
}

/** T1 downward hierarchy flame chart. Levels fill the available viewport and never render labels inside samples. */
export function FlameChart({
  width,
  height,
  title = "RMA_Die",
  data,
  legend = DEFAULT_FLAME_LEGEND,
  palette,
  capabilities,
}: FlameChartProps) {
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
      legend={FLAME_TONES.map((tone, index) => ({
        label: legend[index] ?? DEFAULT_FLAME_LEGEND.at(index) ?? "",
        color: colors[tone],
        marker: colored ? "■" : NO_COLOR_FILL[tone],
      }))}
    >
      {({ width: plotWidth, height: plotHeight }) => {
        const levels = fillLevels(data, plotHeight);
        const rows = levels.map((level): ChartCell[] => {
          const cells: ChartCell[] = Array.from({ length: plotWidth }, () => ({
            character: " ",
            background: colored ? colors.background : undefined,
          }));
          for (const span of aggregateFlameSpans(level, plotWidth)) {
            const start = Math.max(
              0,
              Math.min(plotWidth - 1, Math.floor((span.start / 100) * plotWidth)),
            );
            const end = Math.max(
              start + 1,
              Math.min(plotWidth, Math.ceil((span.end / 100) * plotWidth)),
            );
            const separator = end - start > 1 ? end - 1 : end;
            for (let column = start; column < separator; column += 1)
              cells[column] = colored
                ? { character: " ", background: capabilityColor(colors[span.tone], caps) }
                : { character: NO_COLOR_FILL[span.tone] };
            if (separator < end)
              cells[separator] = {
                character: " ",
                background: colored ? capabilityColor(colors.background, caps) : undefined,
              };
          }
          return cells;
        });
        return (
          <box flexGrow={1} flexDirection="column" overflow="hidden">
            {rows.map((cells, row) => (
              // biome-ignore lint/suspicious/noArrayIndexKey: Flame levels are positional, stateless, and never reordered.
              <CellLine key={row} cells={cells} defaultColor={capabilityColor(colors.text, caps)} />
            ))}
          </box>
        );
      }}
    </ChartFrame>
  );
}

export default FlameChart;
