import type { ChartCapabilities, ChartCell } from "./types.js";

export const BRAILLE_BITS = [
  [0x01, 0x08],
  [0x02, 0x10],
  [0x04, 0x20],
  [0x40, 0x80],
] as const;

export function clamp(value: number, minimum: number, maximum: number): number {
  return Math.max(minimum, Math.min(maximum, value));
}

export function finiteNumber(value: number, fallback = 0): number {
  return Number.isFinite(value) ? value : fallback;
}

export function chartCellWidth(character: string): number {
  const codePoint = character.codePointAt(0) ?? 0;
  if (
    codePoint >= 0x1100 &&
    (codePoint <= 0x115f ||
      codePoint === 0x2329 ||
      codePoint === 0x232a ||
      (codePoint >= 0x2e80 && codePoint <= 0xa4cf && codePoint !== 0x303f) ||
      (codePoint >= 0xac00 && codePoint <= 0xd7a3) ||
      (codePoint >= 0xf900 && codePoint <= 0xfaff) ||
      (codePoint >= 0xfe10 && codePoint <= 0xfe19) ||
      (codePoint >= 0xfe30 && codePoint <= 0xfe6f) ||
      (codePoint >= 0xff00 && codePoint <= 0xff60) ||
      (codePoint >= 0xffe0 && codePoint <= 0xffe6) ||
      (codePoint >= 0x1f300 && codePoint <= 0x1faff))
  )
    return 2;
  return 1;
}

export function chartDisplayWidth(value: string): number {
  return [...value].reduce((total, character) => total + chartCellWidth(character), 0);
}

export function fitChartText(value: string, width: number): string {
  if (width <= 0) return "";
  let output = "";
  let used = 0;
  for (const character of value) {
    const cellWidth = chartCellWidth(character);
    if (used + cellWidth > width) break;
    output += character;
    used += cellWidth;
  }
  return output + " ".repeat(Math.max(0, width - used));
}

export function colorProp<
  T extends "fg" | "bg" | "backgroundColor" | "borderColor" | "titleColor" | "defaultColor",
>(name: T, color: string | undefined): { [K in T]?: string } {
  // Keep this local to the copyable charts boundary. The assertion bridges a computed generic
  // key while omitting undefined colors required by exactOptionalPropertyTypes and NO_COLOR.
  return color === undefined ? {} : ({ [name]: color } as { [K in T]?: string });
}

export function CellLine({
  cells,
  defaultColor,
}: {
  cells: readonly ChartCell[];
  defaultColor?: string | undefined;
}) {
  const runs: Array<{
    color?: string | undefined;
    background?: string | undefined;
    value: string;
  }> = [];
  for (const cell of cells) {
    const previous = runs.at(-1);
    if (previous && previous.color === cell.color && previous.background === cell.background)
      previous.value += cell.character;
    else runs.push({ color: cell.color, background: cell.background, value: cell.character });
  }
  return (
    <text>
      {runs.map((run, index) => (
        <span
          key={`${index}-${run.value}`}
          {...colorProp("fg", run.color ?? defaultColor)}
          {...colorProp("bg", run.background)}
        >
          {run.value}
        </span>
      ))}
    </text>
  );
}

export function capabilityColor(
  color: string,
  capabilities: ChartCapabilities,
): string | undefined {
  return capabilities.colorMode === "none" ? undefined : color;
}

export function createBraillePixels(width: number, height: number): number[][] {
  return Array.from({ length: Math.max(1, Math.floor(height)) }, () =>
    Array.from({ length: Math.max(1, Math.floor(width)) }, () => 0),
  );
}

export function setBraillePixel(pixels: number[][], x: number, y: number): void {
  if (x < 0 || y < 0) return;
  const cellX = Math.floor(x / 2);
  const cellY = Math.floor(y / 4);
  const row = pixels[cellY];
  if (!row || cellX >= row.length) return;
  const bit = BRAILLE_BITS.at(y % 4)?.at(x % 2) ?? 0;
  row[cellX] = (row[cellX] ?? 0) | bit;
}

export function drawBrailleSegment(
  pixels: number[][],
  from: { x: number; y: number },
  to: { x: number; y: number },
): void {
  let x = from.x;
  let y = from.y;
  const dx = Math.abs(to.x - from.x);
  const dy = -Math.abs(to.y - from.y);
  const sx = from.x < to.x ? 1 : -1;
  const sy = from.y < to.y ? 1 : -1;
  let error = dx + dy;
  while (true) {
    setBraillePixel(pixels, x, y);
    if (x === to.x && y === to.y) break;
    const twice = error * 2;
    if (twice >= dy) {
      error += dy;
      x += sx;
    }
    if (twice <= dx) {
      error += dx;
      y += sy;
    }
  }
}

export function brailleCharacter(mask: number, braille = true): string {
  if (!mask) return " ";
  return braille ? String.fromCodePoint(0x2800 + mask) : "•";
}

export function brailleRows(
  pixels: readonly number[][],
  color?: string,
  braille = true,
): ChartCell[][] {
  return pixels.map((row) =>
    row.map((mask) => ({ character: brailleCharacter(mask, braille), color })),
  );
}

export function scaleValue(value: number, minimum: number, maximum: number, span: number): number {
  if (maximum === minimum || span <= 1) return 0;
  return Math.round(((value - minimum) / (maximum - minimum)) * (span - 1));
}
