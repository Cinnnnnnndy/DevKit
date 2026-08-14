import type { KeyEvent, ScrollBoxRenderable } from "@opentui/core";
import { useEffect, useRef } from "react";
import {
  COMPONENT_CONTRACTS,
  COMPONENT_NAMES,
  type ComponentName,
} from "../../components/ui/index.js";
import { colorProp } from "../../components/ui/color-props.js";
import { useUiEnvironment } from "../../components/ui/theme-context.js";

type ComponentInventoryRow = {
  name: ComponentName;
  label: string;
  purpose: string;
  pattern: string;
  textualBase: string;
};

const INVENTORY = [
  ["AgentTimeline", "Agent Timeline", "任务状态流", "P01", "Static + Rich"],
  ["PlanCard", "Plan Card", "任务规划", "P02", "Container"],
  ["EvidenceList", "Evidence List", "证据 + 置信度", "P03", "ListView"],
  ["DiagnosisGraph", "Diagnosis Graph", "因果链路", "P04", "Tree（定制渲染）"],
  ["DiffView", "Diff View", "代码/配置变更", "P05", "RichLog + Syntax"],
  ["MetricVisualization", "Metric Bar / Ranking", "指标", "P06", "ProgressBar / 定制"],
  ["SparklineView", "Sparkline", "内嵌迷你趋势", "P06", "Sparkline（内置）"],
  ["TraceView", "Trace View", "时序泳道", "P07", "定制 Widget"],
  ["KnowledgeCard", "Knowledge Card", "检索问答", "P08", "Markdown"],
  ["CommandPalette", "Command Palette", "命令入口", "P09", "内置 CommandPalette"],
  ["ApprovalBar", "Approval Bar", "确认操作", "P10", "Horizontal + Button"],
  ["ToolCard", "Tool Card", "工具调用", "P11", "Collapsible"],
  ["SummaryCard", "Summary Card", "会话总结", "P12", "Container"],
  ["SelectorPopup", "Selector Popup", "模型/模式/索引选择", "P13–15", "ModalScreen + OptionList"],
  ["SideBlock", "Side Block", "不中断侧问", "P16", "Container"],
  ["CollapsibleOpRow", "Collapsible Op Row", "读写输出折叠", "P18", "Collapsible"],
  ["ContextGauge", "Context Gauge", "上下文占用", "P20", "ProgressBar"],
  ["LiveCanvas", "Live Canvas", "实时指标画布", "P21", "自绘 Canvas"],
  ["HeatmapGrid", "Heatmap Grid", "拓扑热力", "P26", "自绘 Canvas"],
  ["SortableTable", "Sortable Table", "排序/过滤表格", "P24", "DataTable"],
  ["SplitContainer", "Split Container", "可调分栏", "P23", "Container"],
  ["Overlay", "Overlay", "非破坏浮层", "P25", "ModalScreen"],
] as const;

export const COMPONENT_GALLERY_ITEMS = INVENTORY.map(
  ([componentName, label, purpose, pattern, textualBase]) => ({
    name: componentName,
    label,
    purpose,
    pattern,
    textualBase,
    contract: COMPONENT_CONTRACTS[componentName],
  }),
) satisfies readonly (ComponentInventoryRow & {
  contract: (typeof COMPONENT_CONTRACTS)[ComponentName];
})[];

if (COMPONENT_GALLERY_ITEMS.length !== COMPONENT_NAMES.length) {
  throw new Error("Component inventory must cover the 22 canonical components");
}

export interface ComponentGalleryProps {
  width: number;
  height: number;
  onExit?: () => void;
}

export function ComponentGallery({ width, height, onExit }: ComponentGalleryProps) {
  const { theme } = useUiEnvironment();
  const scroll = useRef<ScrollBoxRenderable | null>(null);
  const wide = width >= 100;
  useEffect(() => scroll.current?.focus(), []);
  const onKey = (key: KeyEvent) => {
    const name = key.name.toLowerCase();
    if (name === "escape" || name === "esc") {
      key.preventDefault();
      onExit?.();
      return;
    }
    const box = scroll.current;
    if (!box) return;
    const max = Math.max(0, box.scrollHeight - box.viewport.height);
    const delta =
      name === "down" || name === "j"
        ? 2
        : name === "up" || name === "k"
          ? -2
          : name === "pagedown"
            ? box.viewport.height - 2
            : name === "pageup"
              ? -(box.viewport.height - 2)
              : 0;
    if (name === "home") box.scrollTop = 0;
    else if (name === "end") box.scrollTop = max;
    else if (delta) box.scrollTop = Math.max(0, Math.min(max, box.scrollTop + delta));
    else return;
    key.preventDefault();
    box.requestRender();
  };
  return (
    <box
      width={width}
      height={height}
      paddingX={wide ? 4 : 1}
      paddingTop={1}
      flexDirection="column"
      {...colorProp("backgroundColor", theme.background)}
    >
      <box height={1}>
        <text {...colorProp("fg", theme.primaryText)}>
          <strong>COMPONENTS</strong>
        </text>
      </box>
      <box height={3} justifyContent="center">
        <text {...colorProp("fg", theme.foreground)}>
          <strong>组件清单</strong>
        </text>
      </box>
      <box
        height={2}
        flexDirection="row"
        alignItems="center"
        border={["bottom"]}
        {...colorProp("borderColor", theme.borderStrong)}
        {...colorProp("fg", theme.muted)}
      >
        <text width={wide ? 29 : 24}>组件</text>
        {wide ? <text width={26}>用途</text> : null}
        <text width={8}>TIER</text>
        <text width={13}>PATTERN</text>
        {wide ? <text flexGrow={1}>TEXTUAL 基座</text> : null}
      </box>
      {/* biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI scrollbox has full keyboard scrolling. */}
      <scrollbox
        id="component-gallery-scroll"
        ref={scroll}
        focusable
        focused
        flexGrow={1}
        onKeyDown={onKey}
      >
        {COMPONENT_GALLERY_ITEMS.map((item) => (
          <box
            id={`component-${item.name}`}
            key={item.name}
            height={2}
            flexShrink={0}
            flexDirection="row"
            alignItems="center"
            border={["bottom"]}
            {...colorProp("borderColor", theme.borderSubtle)}
          >
            <text
              width={wide ? 29 : 24}
              wrapMode="none"
              truncate
              {...colorProp("fg", theme.foreground)}
            >
              <strong>{item.label}</strong>
            </text>
            {wide ? (
              <text width={26} wrapMode="none" truncate {...colorProp("fg", theme.secondary)}>
                {item.purpose}
              </text>
            ) : null}
            <text width={8} {...colorProp("fg", theme.secondary)}>
              {item.contract.tier}
            </text>
            <text width={13} {...colorProp("fg", theme.secondary)}>
              {item.pattern}
            </text>
            {wide ? (
              <text flexGrow={1} wrapMode="none" truncate {...colorProp("fg", theme.muted)}>
                {item.textualBase}
              </text>
            ) : null}
          </box>
        ))}
      </scrollbox>
      <text height={1} {...colorProp("fg", theme.muted)}>
        ↑↓/j k · PgUp/PgDn · Home/End · Esc
      </text>
    </box>
  );
}
