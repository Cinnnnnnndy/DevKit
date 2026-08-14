import type {
  AreaDatum,
  BarChartDatum,
  BeforeAfterDatum,
  DigitalNumberDatum,
  DivergingBarChartDatum,
  FlameSpan,
  GroupedBarChartDatum,
  HeatmapRow,
  LineSeries,
  MetricBarDatum,
  ProgressDatum,
  RankingDatum,
  ScatterDatum,
  SegmentedDatum,
  StatDatum,
  TimelineDatum,
  TreeNode,
  WaterlineDatum,
} from "../../components/charts/index.js";

const bar: readonly BarChartDatum[] = [52, 74, 39, 68, 45, 81, 57].map((value, index) => ({
  label: String(index + 1),
  value,
}));
const metricBar: readonly MetricBarDatum[] = [
  { label: "QPS", value: 61, maximum: 80, unit: "k" },
  { label: "CPU", value: 78, maximum: 100, unit: "%" },
];
const ranking: readonly RankingDatum[] = [
  { label: "attention", value: 40, unit: "%" },
  { label: "matmul", value: 25, unit: "%" },
  { label: "layernorm", value: 18, unit: "%" },
  { label: "softmax", value: 10, unit: "%" },
  { label: "copy", value: 7, unit: "%" },
  { label: "reshape", value: 6, unit: "%" },
  { label: "transpose", value: 5, unit: "%" },
  { label: "reduce", value: 4, unit: "%" },
  { label: "cast", value: 3, unit: "%" },
  { label: "other", value: 2, unit: "%" },
];
const beforeAfter: readonly BeforeAfterDatum[] = [
  { label: "P99", before: 120, after: 70, unit: "ms" },
];
const sparkline = [12, 24, 42, 71, 58, 34, 18, 46, 66, 52] as const;
const mirroredArea = {
  up: [20, 48, 64, 38, 72, 51, 80],
  down: [64, 42, 25, 58, 36, 70, 44],
} as const;
const timeline: readonly TimelineDatum[] = [
  { label: "CPU", start: 0, end: 42 },
  { label: "NPU", start: 18, end: 76 },
  { label: "HBM", start: 8, end: 93 },
];
const segmented: readonly SegmentedDatum[] = [
  { label: "used", value: 22 },
  { label: "cache", value: 12 },
  { label: "kv", value: 4 },
  { label: "free", value: 26 },
];
const stat: readonly StatDatum[] = [{ label: "QPS", value: "61k", detail: "+45%" }];
const groupedBar: readonly GroupedBarChartDatum[] = [
  { label: "1", values: [52, 31, 20] },
  { label: "2", values: [76, 48, 35] },
  { label: "3", values: [44, 62, 28] },
  { label: "4", values: [81, 55, 43] },
  { label: "5", values: [63, 39, 52] },
  { label: "6", values: [48, 69, 33] },
];
const divergingBar: readonly DivergingBarChartDatum[] = [
  { label: "1", positive: 45, negative: -52 },
  { label: "2", positive: 68, negative: -73 },
  { label: "3", positive: 82, negative: -61 },
  { label: "4", positive: 56, negative: -88 },
  { label: "5", positive: 74, negative: -67 },
  { label: "6", positive: 63, negative: -79 },
];
const scatter: readonly ScatterDatum[] = [
  { x: 1, y: 28, tone: "red", size: 1 },
  { x: 1.7, y: 42, tone: "orange", size: 2 },
  { x: 2.4, y: 35, tone: "red", size: 1 },
  { x: 3, y: 61, tone: "orange", size: 3 },
  { x: 3.8, y: 55, tone: "green", size: 2 },
  { x: 4.5, y: 72, tone: "green", size: 3 },
  { x: 5.1, y: 48, tone: "orange", size: 1 },
  { x: 6, y: 80, tone: "green", size: 2 },
  { x: 6.8, y: 66, tone: "orange", size: 3 },
];
const line: readonly LineSeries[] = [
  { label: "系列 1", tone: "green", values: [42, 48, 39, 55, 51, 63, 57, 70, 62, 76, 68, 81] },
  { label: "系列 2", tone: "orange", values: [65, 58, 62, 49, 55, 44, 51, 39, 47, 35, 43, 31] },
];
const flameTop: readonly (readonly FlameSpan[])[] = [
  [{ label: "root", start: 0, end: 100, tone: "red" }],
  [
    { label: "root-left", start: 0, end: 15, tone: "red" },
    { label: "main-a", start: 15, end: 47, tone: "green" },
    { label: "main-b", start: 47, end: 53, tone: "green" },
    { label: "main-c", start: 53, end: 100, tone: "green" },
  ],
  [
    { label: "root-left", start: 0, end: 12, tone: "red" },
    { label: "copy", start: 12, end: 15, tone: "cyan" },
    { label: "main-a", start: 15, end: 32, tone: "green" },
    { label: "main-b", start: 32, end: 43, tone: "green" },
    { label: "main-c", start: 43, end: 100, tone: "green" },
  ],
  [
    { label: "root-left", start: 0, end: 17, tone: "red" },
    { label: "main-a", start: 17, end: 33, tone: "green" },
    { label: "main-b", start: 33, end: 39, tone: "green" },
    { label: "main-c", start: 39, end: 100, tone: "green" },
  ],
  [
    { label: "root-left", start: 0, end: 16, tone: "red" },
    { label: "main-a", start: 16, end: 42, tone: "green" },
    { label: "main-b", start: 42, end: 47, tone: "green" },
    { label: "main-c", start: 47, end: 100, tone: "green" },
  ],
  [
    { label: "root-left", start: 0, end: 14, tone: "red" },
    { label: "copy", start: 14, end: 16, tone: "cyan" },
    { label: "main-a", start: 16, end: 58, tone: "green" },
    { label: "main-b", start: 58, end: 98, tone: "green" },
    { label: "edge", start: 98, end: 100, tone: "orange" },
  ],
  [
    { label: "root-left", start: 0, end: 5, tone: "red" },
    { label: "copy", start: 5, end: 16, tone: "cyan" },
    { label: "main-a", start: 16, end: 54, tone: "green" },
    { label: "main-b", start: 54, end: 99, tone: "green" },
  ],
  [
    { label: "root-left", start: 0, end: 4, tone: "red" },
    { label: "copy", start: 5, end: 16, tone: "cyan" },
    { label: "main-a", start: 19, end: 62, tone: "green" },
    { label: "main-b", start: 62, end: 98, tone: "green" },
  ],
  [
    { label: "root-left", start: 0, end: 3, tone: "red" },
    { label: "copy", start: 5, end: 16, tone: "cyan" },
    { label: "main-a", start: 21, end: 55, tone: "green" },
    { label: "main-b", start: 55, end: 97, tone: "green" },
    { label: "edge", start: 98, end: 100, tone: "orange" },
  ],
  [
    { label: "copy", start: 6, end: 16, tone: "cyan" },
    { label: "needle", start: 22, end: 24, tone: "orange" },
    { label: "main", start: 27, end: 96, tone: "green" },
    { label: "edge", start: 97, end: 100, tone: "orange" },
  ],
];

const flameBranches = Array.from({ length: 10 }, (_, offset): readonly FlameSpan[] => {
  const depth = offset + 10;
  const branch = (
    label: string,
    center: number,
    halfWidth: number,
    startDepth: number,
    tone: FlameSpan["tone"],
    tipTone?: FlameSpan["tone"],
  ): FlameSpan | undefined => {
    if (depth < startDepth) return undefined;
    const remaining = halfWidth - (depth - startDepth) * 0.58;
    if (remaining < 0.35) return undefined;
    return {
      label,
      start: center - remaining,
      end: center + remaining,
      tone: tipTone && remaining < 1.8 ? tipTone : tone,
    };
  };
  return [
    branch("left", 12, 3.8, 10, "orange"),
    branch("needle", 23, 1.0, 10, "orange"),
    branch("compute-a", 35, 6.2, 10, "orange"),
    branch("green-a", 31, 2.4, 12, "green"),
    branch("compute-b", 49, 4.6, 11, "orange"),
    branch("green-needle", 57, 2.2, 11, "green"),
    branch("compute-c", 69, 6.0, 10, "orange"),
    branch("green-c", 73, 1.9, 13, "green"),
    branch("compute-d", 84, 5.2, 10, "orange", "red"),
    branch("right", 96, 3.0, 10, "orange", "red"),
  ]
    .filter((span): span is FlameSpan => span !== undefined)
    .sort((left, right) => left.start - right.start);
});

const flame: readonly (readonly FlameSpan[])[] = [...flameTop, ...flameBranches];

const area: readonly AreaDatum[] = Array.from({ length: 145 }, (_, index) => {
  const minute = index * 5;
  const hour = 8 + Math.floor(minute / 60);
  const minuteInHour = minute % 60;
  const baseline =
    1.5 + Math.abs(Math.sin(index * 1.73)) * 2.8 + Math.abs(Math.cos(index * 0.37)) * 1.7;
  const broadMidday = 13 * Math.exp(-(((index - 62) / 10) ** 2));
  const spikes = [
    [6, 24, 0.45],
    [24, 13, 0.65],
    [38, 17, 0.7],
    [71, 27, 0.7],
    [100, 94, 1.35],
    [106, 20, 1.2],
    [112, 13, 0.65],
    [120, 33, 0.55],
    [133, 16, 0.6],
  ] as const;
  const spikeValue = spikes.reduce(
    (total, [center, amplitude, spread]) =>
      total + amplitude * Math.exp(-(((index - center) / spread) ** 2)),
    0,
  );
  return {
    label: `${String(hour).padStart(2, "0")}:${String(minuteInHour).padStart(2, "0")}`,
    value: Math.min(100, Math.round((baseline + broadMidday + spikeValue) * 10) / 10),
  };
});
const waterline: readonly WaterlineDatum[] = [
  { label: "RMA_Die", value: 100, warning: 75, critical: 90, unit: "%" },
  { label: "RMA_Die", value: 62, warning: 80, critical: 92, unit: "%" },
  { label: "RMA_Die", value: 13, warning: 70, critical: 85, unit: "%" },
];
const progress: readonly ProgressDatum[] = [
  { label: "RMA_Die_100", value: 82.38 },
  { label: "DST_1", value: 22.38 },
  { label: "DST_2", value: 40.38 },
  { label: "DST_3", value: 68.38 },
  { label: "DST_4", value: 68.38 },
  { label: "DST_5", value: 68.38 },
  { label: "DST_6", value: 68.38 },
];
const heatmap: readonly HeatmapRow[] = ["一", "二", "三", "四", "五", "六", "日"].map(
  (label, row) => ({
    label: `周${label}`,
    values: Array.from(
      { length: 24 },
      (_, column) => (row * 17 + column * 29 + row * column * 3) % 101,
    ),
  }),
);
const digitalNumber: DigitalNumberDatum = "89:01234567";
const tree: readonly TreeNode[] = [
  {
    id: "root",
    label: "Kunpeng DevKit",
    children: [
      {
        id: "tui",
        label: "tui",
        children: [
          { id: "charts", label: "charts" },
          { id: "components", label: "components" },
        ],
      },
      { id: "service", label: "service" },
      { id: "docs", label: "docs" },
    ],
  },
];

/** 仅供图表画廊使用的确定性 fixture。 */
export const chartGalleryFixtures = {
  metricBar,
  ranking,
  bar,
  groupedBar,
  beforeAfter,
  divergingBar,
  scatter,
  line,
  flame,
  area,
  sparkline,
  mirroredArea,
  timeline,
  waterline,
  progress,
  segmented,
  heatmap,
  digitalNumber,
  stat,
  tree,
} as const;
