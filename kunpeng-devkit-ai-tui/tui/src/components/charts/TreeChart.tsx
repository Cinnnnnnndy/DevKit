import { colorProp, fitChartText } from "./chart-primitives.js";
import { resolveChartPalette } from "./palette.js";
import type { ChartBaseProps } from "./types.js";

export type TreeNode = {
  id: string;
  label: string;
  children?: readonly TreeNode[];
};

export type TreeChartProps = ChartBaseProps & {
  data: readonly TreeNode[];
};

type FlatTreeRow = { key: string; prefix: string; label: string };

function flattenTree(
  nodes: readonly TreeNode[],
  unicode: boolean,
  limit: number,
  ancestors: readonly boolean[] = [],
): FlatTreeRow[] {
  const rows: FlatTreeRow[] = [];
  for (let index = 0; index < nodes.length && rows.length < limit; index += 1) {
    const node = nodes.at(index);
    if (!node) continue;
    const last = index === nodes.length - 1;
    const continuation = ancestors
      .map((hasNext) => (hasNext ? (unicode ? "│  " : "|  ") : "   "))
      .join("");
    const branch =
      ancestors.length === 0 ? "" : last ? (unicode ? "└─ " : "`- ") : unicode ? "├─ " : "+- ";
    rows.push({ key: node.id, prefix: continuation + branch, label: node.label });
    if (node.children?.length && rows.length < limit)
      rows.push(...flattenTree(node.children, unicode, limit - rows.length, [...ancestors, !last]));
  }
  return rows;
}

export function TreeChart({ width, height, data, palette, capabilities }: TreeChartProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const colored = capabilities?.colorMode !== "none";
  const rows = flattenTree(data, capabilities?.unicode !== false, Math.max(0, Math.floor(height)));
  const lineWidth = Math.max(1, width);

  return (
    <box width="100%" height="100%" overflow="hidden" flexDirection="column">
      {rows.map((row) => (
        <text key={row.key} wrapMode="none" {...colorProp("fg", colored ? colors.text : undefined)}>
          {fitChartText(`${row.prefix}${row.label}`, lineWidth)}
        </text>
      ))}
    </box>
  );
}

export default TreeChart;
