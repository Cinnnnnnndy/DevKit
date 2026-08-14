import { colorProp, fitChartText } from "./chart-primitives.js";
import { resolveChartPalette } from "./palette.js";
import { fitPrimitive } from "./primitive-layout.js";
import type { ChartBaseProps } from "./types.js";

export type DigitalNumberDatum = string;

export type DigitalNumberChartProps = ChartBaseProps & {
  data: DigitalNumberDatum;
};

const SEGMENTS: Readonly<Record<string, string>> = {
  "0": "abcdef",
  "1": "bc",
  "2": "abdeg",
  "3": "abcdg",
  "4": "bcfg",
  "5": "acdfg",
  "6": "acdefg",
  "7": "abc",
  "8": "abcdefg",
  "9": "abcdfg",
};

function glyph(character: string, unicode: boolean): string[] {
  if (character === ":") return [" ", unicode ? "•" : ".", " ", unicode ? "•" : ".", " "];
  const active = new Set(SEGMENTS[character] ?? "");
  const horizontal = unicode ? "───" : "---";
  const vertical = unicode ? "│" : "|";
  return [
    active.has("a") ? horizontal : "   ",
    `${active.has("f") ? vertical : " "} ${active.has("b") ? vertical : " "}`,
    active.has("g") ? horizontal : "   ",
    `${active.has("e") ? vertical : " "} ${active.has("c") ? vertical : " "}`,
    active.has("d") ? horizontal : "   ",
  ];
}

export function DigitalNumberChart({
  width,
  height,
  data,
  palette,
  capabilities,
}: DigitalNumberChartProps) {
  const fit = fitPrimitive("pixel-number", width, height);
  if (!fit.fits)
    return (
      <box width={Math.max(1, width)} height={Math.max(1, height)} overflow="hidden">
        <text wrapMode="none" truncate>
          {data}
        </text>
      </box>
    );
  const colors = resolveChartPalette(palette, capabilities);
  const colored = capabilities?.colorMode !== "none";
  const availableDigits = Math.max(1, Math.floor((fit.box.width + 1) / 4));
  const shown = [...data.slice(0, availableDigits)];
  const rows = Array.from({ length: Math.min(5, Math.max(1, fit.box.height)) }, (_, row) =>
    shown.map((character) => glyph(character, capabilities?.unicode !== false)[row]).join(" "),
  );
  const lineWidth = Math.max(1, fit.box.width);

  return (
    <box
      width={fit.box.width}
      height={fit.box.height}
      overflow="hidden"
      flexDirection="column"
      justifyContent={fit.box.height > 7 ? "center" : "flex-start"}
    >
      {rows.map((row, index) => (
        // biome-ignore lint/suspicious/noArrayIndexKey: 七段数码管扫描线具有固定位置、无状态且不会重新排序。
        <text key={index} wrapMode="none" {...colorProp("fg", colored ? colors.white : undefined)}>
          {fitChartText(row, lineWidth)}
        </text>
      ))}
    </box>
  );
}

export const PixelNumberChart = DigitalNumberChart;
export type PixelNumberDatum = DigitalNumberDatum;
export type PixelNumberChartProps = DigitalNumberChartProps;

export default DigitalNumberChart;
