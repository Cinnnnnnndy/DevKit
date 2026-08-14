import type { KeyEvent, ScrollBoxRenderable } from "@opentui/core";
import { useEffect, useRef } from "react";
import {
  AreaChart,
  BeforeAfterChart,
  type ChartCapabilities,
  type ChartPalette,
  FlameChart,
  GroupedBarChart,
  HeatmapChart,
  LineChart,
  MetricBar,
  MirroredAreaChart,
  PixelNumberChart,
  PRIMITIVE_SPECS,
  ProgressChart,
  RankingChart,
  ScatterChart,
  SegmentedChart,
  SparklineChart,
  StatChart,
  TimelineChart,
  WaterlineChart,
} from "../../components/charts/index.js";
import { colorProp } from "../../components/ui/color-props.js";
import { useUiEnvironment } from "../../components/ui/theme-context.js";
import { chartGalleryFixtures } from "./fixtures.js";

export const CHART_GALLERY_ITEMS = [
  { id: "metric-bar", label: "Metric Bar", layer: "T1" },
  { id: "ranking", label: "Ranking", layer: "T1" },
  { id: "grouped-bar", label: "Grouped Bar", layer: "T1" },
  { id: "before-after", label: "Before / After", layer: "T1" },
  { id: "line", label: "Line", layer: "T2" },
  { id: "area", label: "Area", layer: "T2" },
  { id: "sparkline", label: "Sparkline", layer: "T1" },
  { id: "mirrored-area", label: "Mirrored Area", layer: "T2" },
  { id: "scatter", label: "Scatter", layer: "T2" },
  { id: "flame", label: "Flame", layer: "T1" },
  { id: "timeline", label: "Timeline", layer: "T0" },
  { id: "waterline", label: "Waterline", layer: "T1" },
  { id: "progress", label: "Progress", layer: "T1" },
  { id: "segmented", label: "Segmented", layer: "T1" },
  { id: "pixel-number", label: "Pixel Number", layer: "T1" },
  { id: "stat", label: "Stat", layer: "T0" },
  { id: "heatmap", label: "Heatmap", layer: "T3" },
] as const;

export type ChartGalleryProps = {
  width: number;
  height: number;
  palette?: Partial<ChartPalette>;
  capabilities?: Partial<ChartCapabilities>;
  onExit?: () => void;
};

function moveGallery(scroll: ScrollBoxRenderable, position: "start" | "end" | number): void {
  const maximum = Math.max(0, scroll.scrollHeight - scroll.viewport.height);
  scroll.scrollTop =
    position === "start"
      ? 0
      : position === "end"
        ? maximum
        : Math.max(0, Math.min(maximum, scroll.scrollTop + position));
  scroll.requestRender();
}

function galleryKeyHandler(
  scroll: ScrollBoxRenderable | null,
  key: KeyEvent,
  onExit?: () => void,
): void {
  const name = key.name.toLowerCase();
  if (name === "escape" || name === "esc") {
    if (onExit) {
      key.preventDefault();
      onExit();
    }
    return;
  }
  if (!scroll) return;

  const page = Math.max(1, scroll.viewport.height - 2);
  const movement =
    name === "down" || name === "j"
      ? 3
      : name === "up" || name === "k"
        ? -3
        : name === "pagedown"
          ? page
          : name === "pageup"
            ? -page
            : undefined;
  if (movement !== undefined) {
    key.preventDefault();
    moveGallery(scroll, movement);
  } else if (name === "home") {
    key.preventDefault();
    moveGallery(scroll, "start");
  } else if (name === "end") {
    key.preventDefault();
    moveGallery(scroll, "end");
  }
}

type GallerySectionProps = {
  index: number;
  height: number;
  colorEnabled: boolean;
  children: React.ReactNode;
};

function GallerySection({ index, height, colorEnabled, children }: GallerySectionProps) {
  const { theme } = useUiEnvironment();
  const item = CHART_GALLERY_ITEMS[index] ?? { id: "unknown", label: "未知图表", layer: "T0" };
  return (
    <box
      id={`chart-section-${item.id}`}
      width="100%"
      height={height + 5}
      flexShrink={0}
      flexDirection="column"
      {...(index === CHART_GALLERY_ITEMS.length - 1 ? {} : { border: ["bottom"] as const })}
      {...colorProp("borderColor", colorEnabled ? theme.border : undefined)}
    >
      <box
        height={2}
        flexShrink={0}
        paddingX={1}
        {...colorProp("backgroundColor", colorEnabled ? theme.surface2 : undefined)}
        flexDirection="row"
        alignItems="center"
        justifyContent="space-between"
      >
        <text {...colorProp("fg", colorEnabled ? theme.foregroundOnSurface : undefined)}>
          <strong>
            {String(index + 1).padStart(2, "0")} · {item.label}
          </strong>
        </text>
        <text {...colorProp("fg", colorEnabled ? theme.mutedOnSurface : undefined)}>
          {item.layer}
        </text>
      </box>
      <box
        width="100%"
        height={height + 2}
        flexShrink={0}
        paddingX={1}
        paddingY={1}
        overflow="hidden"
      >
        {children}
      </box>
    </box>
  );
}

export function ChartGallery({ width, height, palette, capabilities, onExit }: ChartGalleryProps) {
  const { theme } = useUiEnvironment();
  const gallery = useRef<ScrollBoxRenderable | null>(null);
  const safeWidth = Math.max(1, Math.floor(width));
  const safeHeight = Math.max(1, Math.floor(height));
  const availableChartWidth = Math.max(1, safeWidth - 10);
  const narrow = safeWidth < 80;
  const colorEnabled = capabilities?.colorMode !== "none";
  const unicodeEnabled = capabilities?.unicode !== false;
  const themedPalette: Partial<ChartPalette> = {
    background: theme.background ?? "",
    border: theme.border ?? "",
    text: theme.foregroundOnSurface ?? "",
    white: theme.foreground ?? "",
    blue: theme.copyBlue[2] ?? "",
    green: theme.ubGreen[2] ?? "",
    orange: theme.accumOrange[4] ?? "",
    yellow: theme.mteAmber[2] ?? "",
    red: theme.danger ?? "",
    // Third categorical series uses the l0a-violet ramp (the NPU lane colour in
    // the primitive spec) so it stays distinguishable from blue and green.
    cyan: theme.violet[2] ?? "",
    // Unfilled track / idle cells.
    empty: theme.surface3 ?? "",
    // Waterline and progress fills both mean "healthy / done".
    waterGreen: theme.success ?? "",
    progressGreen: theme.success ?? "",
    heatmap: theme.accumOrange.filter((color): color is string => color !== undefined),
  };
  const shared = {
    palette: { ...themedPalette, ...palette },
    ...(capabilities === undefined ? {} : { capabilities }),
  };
  const recommendedWidth = (id: keyof typeof PRIMITIVE_SPECS) =>
    Math.min(availableChartWidth, PRIMITIVE_SPECS[id].recommended.width);

  useEffect(() => {
    gallery.current?.focus();
  }, []);

  const sections = [
    <MetricBar
      key="metric-bar"
      {...shared}
      width={recommendedWidth("metric-bar")}
      height={2}
      data={chartGalleryFixtures.metricBar}
    />,
    <RankingChart
      key="ranking"
      {...shared}
      width={recommendedWidth("ranking")}
      height={11}
      data={chartGalleryFixtures.ranking}
    />,
    <GroupedBarChart
      key="grouped-bar"
      {...shared}
      width={recommendedWidth("grouped-bar")}
      height={4}
      data={chartGalleryFixtures.groupedBar}
    />,
    <BeforeAfterChart
      key="before-after"
      {...shared}
      width={recommendedWidth("before-after")}
      height={1}
      data={chartGalleryFixtures.beforeAfter}
    />,
    <LineChart
      key="line"
      {...shared}
      width={recommendedWidth("line")}
      height={6}
      data={chartGalleryFixtures.line}
    />,
    <AreaChart
      key="area"
      {...shared}
      width={recommendedWidth("area")}
      height={5}
      data={chartGalleryFixtures.area}
    />,
    <SparklineChart
      key="sparkline"
      {...shared}
      width={recommendedWidth("sparkline")}
      height={1}
      data={chartGalleryFixtures.sparkline}
      label="Latency"
    />,
    <MirroredAreaChart
      key="mirrored-area"
      {...shared}
      width={recommendedWidth("mirrored-area")}
      height={4}
      up={chartGalleryFixtures.mirroredArea.up}
      down={chartGalleryFixtures.mirroredArea.down}
    />,
    <ScatterChart
      key="scatter"
      {...shared}
      width={recommendedWidth("scatter")}
      height={12}
      data={chartGalleryFixtures.scatter}
    />,
    <FlameChart
      key="flame"
      {...shared}
      width={recommendedWidth("flame")}
      height={8}
      data={chartGalleryFixtures.flame}
    />,
    <TimelineChart
      key="timeline"
      {...shared}
      width={recommendedWidth("timeline")}
      height={6}
      data={chartGalleryFixtures.timeline}
    />,
    <WaterlineChart
      key="waterline"
      {...shared}
      width={recommendedWidth("waterline")}
      height={8}
      data={chartGalleryFixtures.waterline}
    />,
    <ProgressChart
      key="progress"
      {...shared}
      width={recommendedWidth("progress")}
      height={2}
      data={chartGalleryFixtures.progress}
    />,
    <SegmentedChart
      key="segmented"
      {...shared}
      width={recommendedWidth("segmented")}
      height={2}
      data={chartGalleryFixtures.segmented}
    />,
    <PixelNumberChart
      key="pixel-number"
      {...shared}
      width={recommendedWidth("pixel-number")}
      height={5}
      data={chartGalleryFixtures.digitalNumber}
    />,
    <StatChart
      key="stat"
      {...shared}
      width={recommendedWidth("stat")}
      height={1}
      data={chartGalleryFixtures.stat}
    />,
    <HeatmapChart
      key="heatmap"
      {...shared}
      width={recommendedWidth("heatmap")}
      height={6}
      data={chartGalleryFixtures.heatmap}
    />,
  ] as const;
  const sectionHeights = [2, 11, 4, 1, 6, 5, 1, 4, 12, 8, 6, 8, 2, 2, 5, 1, 6] as const;

  return (
    <box
      width={safeWidth}
      height={safeHeight}
      flexDirection="column"
      {...colorProp("backgroundColor", colorEnabled ? theme.surface1 : undefined)}
    >
      <box
        height={3}
        flexShrink={0}
        paddingX={2}
        border={["bottom"]}
        {...colorProp("borderColor", colorEnabled ? theme.border : undefined)}
        {...colorProp("backgroundColor", colorEnabled ? theme.background : undefined)}
        flexDirection="row"
        alignItems="center"
        justifyContent="space-between"
      >
        <text {...colorProp("fg", colorEnabled ? theme.foreground : undefined)}>
          <strong>图表原语库 · 十七种画法</strong>{" "}
          <span {...colorProp("fg", colorEnabled ? theme.muted : undefined)}>· 推荐尺寸即停</span>
        </text>
        <text {...colorProp("fg", colorEnabled ? theme.muted : undefined)}>
          {narrow
            ? unicodeEnabled
              ? "单列 · 17 种"
              : "单列 / 17 种"
            : unicodeEnabled
              ? "最小尺寸 · 推荐尺寸 · 收缩判决"
              : "minimum / recommended / fallback"}
        </text>
      </box>
      {/* biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI 滚动框可聚焦，并提供完整的键盘滚动。 */}
      <scrollbox
        id="chart-gallery-scroll"
        ref={gallery}
        height={Math.max(1, safeHeight - 5)}
        flexGrow={1}
        focusable
        focused
        verticalScrollbarOptions={{ visible: colorEnabled }}
        onKeyDown={(key) => galleryKeyHandler(gallery.current, key, onExit)}
      >
        {CHART_GALLERY_ITEMS.map((item, index) => (
          <GallerySection
            key={item.id}
            index={index}
            height={sectionHeights[index] ?? 1}
            colorEnabled={colorEnabled}
          >
            {sections[index]}
          </GallerySection>
        ))}
      </scrollbox>
      <box
        height={2}
        flexShrink={0}
        paddingX={2}
        border={["top"]}
        {...colorProp("borderColor", colorEnabled ? theme.border : undefined)}
        {...colorProp("backgroundColor", colorEnabled ? theme.background : undefined)}
        alignItems="center"
      >
        <text {...colorProp("fg", colorEnabled ? theme.muted : undefined)}>
          {unicodeEnabled
            ? "↑↓ / j k 滚动 · PgUp/PgDn 翻页 · Home/End 首尾 · 鼠标滚轮 · Esc 返回"
            : "Up/Down / j k 滚动 / PgUp/PgDn 翻页 / Home/End 首尾 / Esc 返回"}
        </text>
      </box>
    </box>
  );
}
