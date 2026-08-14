export type PrimitiveId =
  | "metric-bar"
  | "ranking"
  | "grouped-bar"
  | "before-after"
  | "line"
  | "area"
  | "sparkline"
  | "mirrored-area"
  | "scatter"
  | "flame"
  | "timeline"
  | "waterline"
  | "progress"
  | "segmented"
  | "pixel-number"
  | "stat"
  | "heatmap";

export type PrimitiveTier = "T0" | "T1" | "T2" | "T3";

export type PrimitiveFallback =
  | { kind: "primitive"; primitive: PrimitiveId; description: string }
  | { kind: "text"; description: string }
  | { kind: "layout"; description: string };

export interface PrimitiveSize {
  width: number;
  height: number;
}

export interface PrimitiveAspect {
  min: number;
  max: number;
}

export interface PrimitiveSpec {
  id: PrimitiveId;
  label: string;
  tier: PrimitiveTier;
  minimum: PrimitiveSize;
  recommended: PrimitiveSize;
  shrinkPriority: 1 | 2 | 3 | 4;
  aspect?: PrimitiveAspect;
  evenRows?: boolean;
  fallback: PrimitiveFallback;
}

const text = (description: string): PrimitiveFallback => ({ kind: "text", description });
const layout = (description: string): PrimitiveFallback => ({ kind: "layout", description });
const primitive = (primitiveId: PrimitiveId, description: string): PrimitiveFallback => ({
  kind: "primitive",
  primitive: primitiveId,
  description,
});

export const PRIMITIVE_SPECS = {
  "metric-bar": spec(
    "metric-bar",
    "Metric Bar",
    "T1",
    10,
    1,
    20,
    1,
    1,
    text("label + value + percent"),
  ),
  ranking: spec("ranking", "Ranking", "T1", 24, 4, 34, 11, 3, text("sorted label and value list")),
  "grouped-bar": spec(
    "grouped-bar",
    "Grouped Bar",
    "T1",
    17,
    3,
    26,
    4,
    2,
    layout("independent Metric Bars with the shared scale stated in text"),
  ),
  "before-after": spec(
    "before-after",
    "Before / After",
    "T1",
    24,
    1,
    32,
    1,
    2,
    text("before value, after value, and signed delta"),
  ),
  line: spec(
    "line",
    "Line",
    "T2",
    20,
    3,
    40,
    6,
    3,
    primitive("sparkline", "Sparkline plus latest value"),
    {
      min: 5,
      max: 24,
    },
  ),
  area: spec(
    "area",
    "Area",
    "T2",
    20,
    2,
    40,
    5,
    2,
    primitive("sparkline", "Sparkline plus aggregate value"),
    {
      min: 5,
      max: 24,
    },
  ),
  sparkline: spec(
    "sparkline",
    "Sparkline",
    "T1",
    8,
    1,
    20,
    1,
    1,
    text("minimum, latest, and maximum values"),
  ),
  "mirrored-area": spec(
    "mirrored-area",
    "Mirrored Area",
    "T2",
    20,
    2,
    40,
    4,
    2,
    layout("two labeled Sparklines with independent direction glyphs"),
    { min: 5, max: 24 },
    true,
  ),
  scatter: spec(
    "scatter",
    "Scatter",
    "T2",
    16,
    8,
    24,
    12,
    3,
    text("correlation verdict, sample count, and outlier count"),
    { min: 2, max: 2 },
  ),
  flame: spec(
    "flame",
    "Flame",
    "T1",
    30,
    3,
    60,
    8,
    4,
    layout("Top-N hot-function table with percentages"),
  ),
  timeline: spec(
    "timeline",
    "Timeline",
    "T0",
    30,
    3,
    56,
    6,
    4,
    layout("lane occupancy and duration summary"),
  ),
  waterline: spec(
    "waterline",
    "Waterline",
    "T1",
    3,
    4,
    3,
    8,
    1,
    text("current value, capacity, and percent"),
    { min: 0.25, max: 0.8 },
  ),
  progress: spec(
    "progress",
    "Progress",
    "T1",
    12,
    1,
    28,
    1,
    1,
    text("current, total, and percent"),
  ),
  segmented: spec(
    "segmented",
    "Segmented",
    "T1",
    16,
    2,
    30,
    2,
    1,
    text("segment labels and values"),
  ),
  "pixel-number": spec(
    "pixel-number",
    "Pixel Number",
    "T1",
    11,
    5,
    19,
    5,
    1,
    text("plain numeric value"),
  ),
  stat: spec("stat", "Stat", "T0", 18, 1, 32, 1, 1, text("label and value")),
  heatmap: spec(
    "heatmap",
    "Heatmap",
    "T3",
    16,
    4,
    32,
    6,
    4,
    layout("four NUMA rows with numeric range and hotspot markers"),
  ),
} as const satisfies Record<PrimitiveId, PrimitiveSpec>;

export const PRIMITIVE_IDS: readonly PrimitiveId[] = Object.freeze(
  Object.keys(PRIMITIVE_SPECS) as PrimitiveId[],
);

export interface ChartBoxOptions {
  paddingX?: number;
  paddingY?: number;
  border?: boolean;
}

export interface ChartBox {
  width: number;
  height: number;
  innerWidth: number;
  innerHeight: number;
}

/** 规范化终端矩形，并计算可绘制的单元格区域。 */
export function chartBox(width: number, height: number, options: ChartBoxOptions = {}): ChartBox {
  const safeWidth = cellCount(width);
  const safeHeight = cellCount(height);
  const border = options.border === true ? 1 : 0;
  const horizontalInset = border * 2 + cellCount(options.paddingX ?? 0) * 2;
  const verticalInset = border * 2 + cellCount(options.paddingY ?? 0) * 2;
  return {
    width: safeWidth,
    height: safeHeight,
    innerWidth: Math.max(0, safeWidth - horizontalInset),
    innerHeight: Math.max(0, safeHeight - verticalInset),
  };
}

export type PrimitiveFitLevel = "recommended" | "compact" | "minimum" | "fallback";

export interface PrimitiveFitResult {
  id: PrimitiveId;
  box: PrimitiveSize;
  level: PrimitiveFitLevel;
  fits: boolean;
  fallback?: PrimitiveFallback;
}

/** 根据宽高比和行约束适配并裁剪图元。 */
export function fitPrimitive(
  primitiveInput: PrimitiveId | PrimitiveSpec,
  width: number,
  height: number,
): PrimitiveFitResult {
  const resolved = resolveSpec(primitiveInput);
  const box = cropToConstraints({ width: cellCount(width), height: cellCount(height) }, resolved);
  if (!contains(box, resolved.minimum)) {
    return { id: resolved.id, box, level: "fallback", fits: false, fallback: resolved.fallback };
  }
  if (contains(box, resolved.recommended)) {
    return { id: resolved.id, box, level: "recommended", fits: true };
  }
  const oneAxisAtMinimum =
    box.width === resolved.minimum.width || box.height === resolved.minimum.height;
  return { id: resolved.id, box, level: oneAxisAtMinimum ? "minimum" : "compact", fits: true };
}

/**
 * 将应优先让出空间的图元排序。优先级相同时按推荐区域从大到小排序；
 * 完全相等时保持输入顺序。
 */
export function shrinkOrder(
  primitives: readonly (PrimitiveId | PrimitiveSpec)[],
): readonly PrimitiveSpec[] {
  return primitives
    .map((primitiveInput, index) => ({ spec: resolveSpec(primitiveInput), index }))
    .sort(
      (left, right) =>
        left.spec.shrinkPriority - right.spec.shrinkPriority ||
        area(right.spec.recommended) - area(left.spec.recommended) ||
        left.index - right.index,
    )
    .map(({ spec: primitiveSpec }) => primitiveSpec);
}

function spec(
  id: PrimitiveId,
  label: string,
  tier: PrimitiveTier,
  minimumWidth: number,
  minimumHeight: number,
  recommendedWidth: number,
  recommendedHeight: number,
  shrinkPriority: 1 | 2 | 3 | 4,
  fallback: PrimitiveFallback,
  aspect?: PrimitiveAspect,
  evenRows?: boolean,
): PrimitiveSpec {
  return {
    id,
    label,
    tier,
    minimum: { width: minimumWidth, height: minimumHeight },
    recommended: { width: recommendedWidth, height: recommendedHeight },
    shrinkPriority,
    ...(aspect === undefined ? {} : { aspect }),
    ...(evenRows === undefined ? {} : { evenRows }),
    fallback,
  };
}

function resolveSpec(primitiveInput: PrimitiveId | PrimitiveSpec): PrimitiveSpec {
  return typeof primitiveInput === "string" ? PRIMITIVE_SPECS[primitiveInput] : primitiveInput;
}

function cropToConstraints(box: PrimitiveSize, primitiveSpec: PrimitiveSpec): PrimitiveSize {
  let width = box.width;
  let height = primitiveSpec.evenRows === true ? box.height - (box.height % 2) : box.height;
  const aspect = primitiveSpec.aspect;
  if (aspect !== undefined && width > 0 && height > 0) {
    if (width / height > aspect.max) width = Math.floor(height * aspect.max);
    if (width / height < aspect.min) height = Math.floor(width / aspect.min);
    if (primitiveSpec.evenRows === true && height % 2 !== 0) height -= 1;
  }
  return { width: Math.max(0, width), height: Math.max(0, height) };
}

function cellCount(value: number): number {
  return Number.isFinite(value) ? Math.max(0, Math.floor(value)) : 0;
}

function contains(box: PrimitiveSize, size: PrimitiveSize): boolean {
  return box.width >= size.width && box.height >= size.height;
}

function area(size: PrimitiveSize): number {
  return size.width * size.height;
}
