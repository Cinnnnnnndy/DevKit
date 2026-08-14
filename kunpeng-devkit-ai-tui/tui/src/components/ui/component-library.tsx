import type { ReactNode } from "react";
import { HeatmapChart, MetricBar, SparklineChart } from "../charts/index.js";
import { colorProp } from "./color-props.js";
import { OverlayScrim } from "./overlays.js";
import { useUiEnvironment } from "./theme-context.js";
import type { ComponentContract, ComponentState, RenderTier } from "./types.js";

export const COMPONENT_REFERENCE = "web-feasibility-2026-08-13" as const;
export type ComponentName =
  | "AgentTimeline"
  | "PlanCard"
  | "EvidenceList"
  | "DiagnosisGraph"
  | "DiffView"
  | "MetricVisualization"
  | "SparklineView"
  | "TraceView"
  | "KnowledgeCard"
  | "CommandPalette"
  | "ApprovalBar"
  | "ToolCard"
  | "SummaryCard"
  | "SelectorPopup"
  | "SideBlock"
  | "CollapsibleOpRow"
  | "ContextGauge"
  | "LiveCanvas"
  | "HeatmapGrid"
  | "SortableTable"
  | "SplitContainer"
  | "Overlay";

const states = [
  "default",
  "focused",
  "selected",
  "disabled",
  "loading",
  "empty",
  "loaded",
  "error",
  "failed",
  "cancelled",
] as const satisfies readonly ComponentState[];
function contract(
  tier: RenderTier,
  keys: readonly string[],
  to: RenderTier = "T0",
): ComponentContract {
  return {
    tier,
    states,
    keyboardEquivalents: keys,
    tokens: ["surface1", "foreground", "border", "focus"],
    degradation:
      tier === to
        ? []
        : [{ reason: "ssh", from: tier, to, preserves: "labels, values, and status glyphs" }],
  };
}
export const COMPONENT_CONTRACTS = {
  AgentTimeline: contract("T0", ["↑/↓", "Enter"]),
  PlanCard: contract("T0", ["Space", "Enter"]),
  EvidenceList: contract("T1", ["↑/↓", "Enter"]),
  DiagnosisGraph: contract("T0", ["↑/↓", "Enter"]),
  DiffView: contract("T0", ["PgUp/PgDn"]),
  MetricVisualization: contract("T1", ["↑/↓"]),
  SparklineView: contract("T1", ["←/→"]),
  TraceView: contract("T3", ["←/→", "+/-"], "T1"),
  KnowledgeCard: contract("T0", ["Enter"]),
  CommandPalette: contract("T4", ["Ctrl+P", "↑/↓", "Enter", "Esc"], "T0"),
  ApprovalBar: contract("T0", ["A", "R", "N"]),
  ToolCard: contract("T0", ["Space"]),
  SummaryCard: contract("T0", ["Enter"]),
  SelectorPopup: contract("T4", ["↑/↓", "Enter", "Esc"], "T0"),
  SideBlock: contract("T0", ["Enter"]),
  CollapsibleOpRow: contract("T0", ["Space"]),
  ContextGauge: contract("T1", ["Enter"]),
  LiveCanvas: contract("T2", ["Space", "[/]"], "T1"),
  HeatmapGrid: contract("T3", ["Arrow keys", "Enter"], "T1"),
  SortableTable: contract("T4", ["←/→", "Enter"], "T0"),
  SplitContainer: contract("T4", ["Ctrl+←/→"], "T0"),
  Overlay: contract("T4", ["Esc", "Tab"], "T0"),
} as const satisfies Record<ComponentName, ComponentContract>;
export const COMPONENT_NAMES = Object.freeze(Object.keys(COMPONENT_CONTRACTS) as ComponentName[]);

export interface CommonComponentProps {
  state?: ComponentState;
  width?: number;
  height?: number;
}
function Frame({
  title,
  state = "loaded",
  width,
  height,
  children,
  onPress,
}: CommonComponentProps & {
  title: string;
  children: ReactNode;
  onPress?: (() => void) | undefined;
}) {
  const { theme } = useUiEnvironment();
  const disabled = state === "disabled";
  return (
    <box
      width={width ?? "100%"}
      height={height ?? 5}
      border
      flexDirection="column"
      overflow="hidden"
      {...colorProp("borderColor", state === "focused" ? theme.borderStrong : theme.border)}
      {...colorProp("backgroundColor", state === "selected" ? theme.selected : theme.surface1)}
      {...(!disabled && onPress ? { onMouseDown: onPress } : {})}
    >
      <text
        wrapMode="none"
        truncate
        {...colorProp("fg", disabled ? theme.disabled : theme.foreground)}
      >
        <strong>{title}</strong> · {state}
      </text>
      <box flexGrow={1} minHeight={1} flexDirection="column" overflow="hidden">
        {children}
      </box>
    </box>
  );
}
export type TimelineItem = { label: string; status: string; detail?: string };
export function AgentTimeline({
  items,
  patternId,
  description,
  note,
  width,
  height,
}: CommonComponentProps & {
  items: readonly TimelineItem[];
  patternId?: string;
  description?: string;
  note?: string;
}) {
  const { theme } = useUiEnvironment();
  const safeWidth = typeof width === "number" ? width : 80;
  const labelWidth = Math.max(12, Math.min(31, safeWidth - 12));
  const statusColor = (status: string) => {
    if (status === "●") return theme.success;
    if (status === "▶") return theme.primaryText;
    if (status === "✕") return theme.danger;
    return theme.muted;
  };
  return (
    <box
      width={width ?? "100%"}
      height={height ?? 14}
      border
      flexDirection="column"
      overflow="hidden"
      {...colorProp("borderColor", theme.border)}
      {...colorProp("backgroundColor", theme.surface1)}
    >
      <box
        height={3}
        paddingX={1}
        flexDirection="row"
        alignItems="center"
        border={["bottom"]}
        {...colorProp("borderColor", theme.border)}
        {...colorProp("backgroundColor", theme.surface2)}
      >
        {patternId ? (
          <text marginRight={1} {...colorProp("fg", theme.primaryText)}>
            <strong>{patternId}</strong>
          </text>
        ) : null}
        <text flexGrow={1} wrapMode="none" truncate {...colorProp("fg", theme.foreground)}>
          <strong>Agent Timeline</strong>
        </text>
        {description && safeWidth >= 70 ? (
          <text wrapMode="none" truncate {...colorProp("fg", theme.muted)}>
            {description}
          </text>
        ) : null}
      </box>
      <box
        flexGrow={1}
        minHeight={1}
        paddingX={2}
        paddingTop={1}
        flexDirection="column"
        overflow="hidden"
        {...colorProp("backgroundColor", theme.backgroundOuter)}
      >
        {items.map((item) => (
          <box key={item.label} height={1} flexDirection="row">
            <text width={2} {...colorProp("fg", statusColor(item.status))}>
              {item.status}
            </text>
            <text
              width={labelWidth}
              wrapMode="none"
              truncate
              {...colorProp("fg", theme.foreground)}
            >
              {item.label}
            </text>
            {item.detail ? (
              <text wrapMode="none" truncate {...colorProp("fg", theme.muted)}>
                {item.detail}
              </text>
            ) : null}
          </box>
        ))}
      </box>
      {note ? (
        <box
          height={2}
          paddingX={2}
          flexDirection="row"
          alignItems="center"
          {...colorProp("backgroundColor", theme.surface1)}
        >
          <text marginRight={1} {...colorProp("fg", theme.primaryText)}>
            ▏
          </text>
          <text flexGrow={1} wrapMode="none" truncate {...colorProp("fg", theme.muted)}>
            {note}
          </text>
        </box>
      ) : null}
    </box>
  );
}
export function PlanCard({
  title = "Plan",
  steps,
  onExecute,
  patternId,
  description,
  lines,
  actions,
  width,
  height,
  ...props
}: CommonComponentProps & {
  title?: string;
  steps: readonly string[];
  onExecute?: () => void;
  patternId?: string;
  description?: string;
  lines?: readonly string[];
  actions?: readonly { key: string; label: string }[];
}) {
  const { theme } = useUiEnvironment();
  const safeWidth = typeof width === "number" ? width : 80;
  if (patternId) {
    return (
      <box
        width={width ?? "100%"}
        height={height ?? 14}
        border
        flexDirection="column"
        overflow="hidden"
        {...colorProp("borderColor", theme.border)}
        {...colorProp("backgroundColor", theme.surface1)}
        {...(onExecute ? { onMouseDown: onExecute } : {})}
      >
        <box
          height={3}
          paddingX={1}
          flexDirection="row"
          alignItems="center"
          border={["bottom"]}
          {...colorProp("borderColor", theme.border)}
          {...colorProp("backgroundColor", theme.surface2)}
        >
          <text marginRight={1} {...colorProp("fg", theme.primaryText)}>
            <strong>{patternId}</strong>
          </text>
          <text flexGrow={1} wrapMode="none" truncate {...colorProp("fg", theme.foreground)}>
            <strong>{title}</strong>
          </text>
          {description && safeWidth >= 70 ? (
            <text wrapMode="none" truncate {...colorProp("fg", theme.muted)}>
              {description}
            </text>
          ) : null}
        </box>
        <box
          flexGrow={1}
          minHeight={1}
          paddingX={2}
          paddingTop={1}
          flexDirection="column"
          overflow="hidden"
          {...colorProp("backgroundColor", theme.backgroundOuter)}
        >
          {(lines ?? steps.map((step, index) => `${index + 1}. ${step}`)).map((line) => (
            <text key={line} wrapMode="none" truncate {...colorProp("fg", theme.foreground)}>
              {line}
            </text>
          ))}
          {actions ? (
            <box marginTop={1} flexDirection="row">
              {actions.map((action, index) => (
                <text key={action.key} marginRight={index < actions.length - 1 ? 3 : 0}>
                  <span {...colorProp("fg", theme.primaryText)}>[{action.key}]</span>
                  <span {...colorProp("fg", theme.foreground)}>{action.label}</span>
                </text>
              ))}
            </box>
          ) : null}
        </box>
      </box>
    );
  }
  return (
    <Frame
      title={title}
      {...(width === undefined ? {} : { width })}
      {...(height === undefined ? {} : { height })}
      {...props}
      onPress={onExecute}
    >
      {steps.map((step, index) => (
        <text key={step} wrapMode="none" truncate>
          {index + 1}. {step}
        </text>
      ))}
    </Frame>
  );
}
export function EvidenceList({
  items,
  onSelect,
  ...props
}: CommonComponentProps & {
  items: readonly { id: string; label: string; confidence: number }[];
  onSelect?: (id: string) => void;
}) {
  return (
    <Frame title="Evidence" {...props}>
      {items.map((item) => (
        // biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI 行提供组件合同声明的键盘路径。
        <text key={item.id} onMouseDown={() => onSelect?.(item.id)} wrapMode="none" truncate>
          ▎ {item.label} · {item.confidence}%
        </text>
      ))}
    </Frame>
  );
}
export function DiagnosisGraph({
  nodes,
  ...props
}: CommonComponentProps & { nodes: readonly string[] }) {
  return (
    <Frame title="Diagnosis Graph" {...props}>
      {nodes.map((node, index) => (
        <text key={node}>
          {index ? "  └─▸" : "▸"} {node}
        </text>
      ))}
    </Frame>
  );
}
export function DiffView({ lines, ...props }: CommonComponentProps & { lines: readonly string[] }) {
  const { theme } = useUiEnvironment();
  return (
    <Frame title="Diff" {...props}>
      {lines.map((line, index) => (
        <text
          key={`${index}-${line}`}
          {...colorProp(
            "fg",
            line.startsWith("+")
              ? theme.success
              : line.startsWith("-")
                ? theme.danger
                : theme.secondary,
          )}
        >
          {line}
        </text>
      ))}
    </Frame>
  );
}
export function MetricVisualization({
  data,
  ...props
}: CommonComponentProps & {
  data: readonly { label: string; value: number; maximum?: number; unit?: string }[];
}) {
  return (
    <Frame title="Metric / Ranking" {...props}>
      <MetricBar
        width={Math.max(10, (props.width ?? 42) - 2)}
        height={Math.max(1, (props.height ?? 6) - 2)}
        data={data}
      />
    </Frame>
  );
}
export function SparklineView({
  values,
  label = "Latency",
  ...props
}: CommonComponentProps & { values: readonly number[]; label?: string }) {
  return (
    <Frame title="Sparkline" {...props}>
      <SparklineChart
        width={Math.max(8, (props.width ?? 42) - 2)}
        height={1}
        data={values}
        label={label}
      />
    </Frame>
  );
}
export function TraceView({
  lanes,
  selected = 0,
  onSelect,
  ...props
}: CommonComponentProps & {
  lanes: readonly { label: string; value: string }[];
  selected?: number;
  onSelect?: (index: number) => void;
}) {
  return (
    <Frame title="Trace View" {...props}>
      {lanes.map((lane, index) => (
        // biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI 轨道选择同样提供方向键选择路径。
        <text key={lane.label} onMouseDown={() => onSelect?.(index)}>
          {index === selected ? "▸" : " "} {lane.label} {lane.value}
        </text>
      ))}
    </Frame>
  );
}
export function KnowledgeCard({
  title,
  answer,
  source,
  ...props
}: CommonComponentProps & { title: string; answer: string; source: string }) {
  return (
    <Frame title={title} {...props}>
      <text wrapMode="word">{answer}</text>
      <text>↗ {source}</text>
    </Frame>
  );
}
export function ApprovalBar({
  selected = "review",
  onResolve,
  ...props
}: CommonComponentProps & {
  selected?: "approve" | "review" | "reject";
  onResolve?: (value: "approve" | "review" | "reject") => void;
}) {
  return (
    <Frame title="Approval" {...props}>
      {(["approve", "review", "reject"] as const).map((value) => (
        // biome-ignore lint/a11y/noStaticElementInteractions: A/R/N 是等价的键盘审批路径。
        <text key={value} onMouseDown={() => onResolve?.(value)}>
          {value === selected ? "▸" : " "} [
          {value === "approve" ? "A" : value === "review" ? "R" : "N"}] {value}
        </text>
      ))}
    </Frame>
  );
}
export function ToolCard({
  name,
  detail,
  expanded = false,
  onToggle,
  ...props
}: CommonComponentProps & {
  name: string;
  detail: string;
  expanded?: boolean;
  onToggle?: () => void;
}) {
  return (
    <Frame title={`Tool · ${name}`} {...props} onPress={onToggle}>
      <text>
        {expanded ? "▼" : "▶"} {detail}
      </text>
      {expanded ? <text>stdout · completed</text> : null}
    </Frame>
  );
}
export function SummaryCard({
  rows,
  ...props
}: CommonComponentProps & { rows: readonly string[] }) {
  return (
    <Frame title="Summary" {...props}>
      {rows.map((row) => (
        <text key={row}>✓ {row}</text>
      ))}
    </Frame>
  );
}
export function SelectorPopup({
  options,
  selected = 0,
  onSelect,
  ...props
}: CommonComponentProps & {
  options: readonly string[];
  selected?: number;
  onSelect?: (index: number) => void;
}) {
  return (
    <Frame title="Selector" {...props}>
      {options.map((option, index) => (
        // biome-ignore lint/a11y/noStaticElementInteractions: 选择器同样提供方向键和 Enter 操作。
        <text key={option} onMouseDown={() => onSelect?.(index)}>
          {index === selected ? "▸" : " "} {option}
        </text>
      ))}
    </Frame>
  );
}
export function SideBlock({
  question,
  answer,
  ...props
}: CommonComponentProps & { question: string; answer: string }) {
  return (
    <Frame title="Side Block" {...props}>
      <text>Q {question}</text>
      <text>A {answer}</text>
    </Frame>
  );
}
export function CollapsibleOpRow({
  label,
  expanded = false,
  onToggle,
  ...props
}: CommonComponentProps & { label: string; expanded?: boolean; onToggle?: () => void }) {
  return (
    <Frame title="Operation" {...props} onPress={onToggle}>
      <text>
        {expanded ? "▼" : "▶"} {label}
      </text>
      {expanded ? <text>command · duration · result</text> : null}
    </Frame>
  );
}
export function ContextGauge({
  value,
  maximum = 100,
  ...props
}: CommonComponentProps & { value: number; maximum?: number }) {
  return (
    <MetricVisualization {...props} data={[{ label: "Context", value, maximum, unit: "%" }]} />
  );
}
export function LiveCanvas({
  samples,
  frozen = false,
  rate = "1s",
  onToggleFreeze,
  onRate,
  ...props
}: CommonComponentProps & {
  samples: readonly number[];
  frozen?: boolean;
  rate?: string;
  onToggleFreeze?: () => void;
  onRate?: (rate: string) => void;
}) {
  return (
    <Frame
      title={`Live Canvas · ${rate} · ${frozen ? "FROZEN" : "LIVE"}`}
      {...props}
      onPress={onToggleFreeze}
    >
      <SparklineChart
        width={Math.max(8, (props.width ?? 42) - 2)}
        height={1}
        data={samples}
        label="live"
      />
      <text wrapMode="none" truncate>
        {rate} · {frozen ? "FROZEN" : "LIVE"}
      </text>
      {/* biome-ignore lint/a11y/noStaticElementInteractions: 方括号键提供等价的采样率调节路径。 */}
      <text onMouseDown={() => onRate?.(rate === "1s" ? "5s" : "1s")}>
        Space freeze · [/] sampling
      </text>
    </Frame>
  );
}
export function HeatmapGrid({
  data,
  annotation = false,
  onToggleAnnotation,
  ...props
}: CommonComponentProps & {
  data: readonly { label: string; values: readonly number[] }[];
  annotation?: boolean;
  onToggleAnnotation?: () => void;
}) {
  return (
    <Frame
      title={`Heatmap Grid${annotation ? " · AI annotation" : ""}`}
      {...props}
      onPress={onToggleAnnotation}
    >
      <HeatmapChart
        width={Math.max(16, (props.width ?? 42) - 2)}
        height={Math.max(4, (props.height ?? 8) - 2)}
        data={data}
      />
    </Frame>
  );
}
export function SortableTable({
  rows,
  sort = "value",
  onSort,
  ...props
}: CommonComponentProps & {
  rows: readonly { name: string; value: number }[];
  sort?: "name" | "value";
  onSort?: (sort: "name" | "value") => void;
}) {
  const sorted = [...rows].sort(
    sort === "value" ? (a, b) => b.value - a.value : (a, b) => a.name.localeCompare(b.name),
  );
  return (
    <Frame
      title={`Sortable Table · ${sort}`}
      {...props}
      onPress={() => onSort?.(sort === "value" ? "name" : "value")}
    >
      {sorted.map((row) => (
        <text key={row.name}>
          {row.name.padEnd(14)} {row.value}
        </text>
      ))}
    </Frame>
  );
}
export function SplitContainer({
  preset = "analysis",
  left,
  right,
  onPreset,
  ...props
}: CommonComponentProps & {
  preset?: string;
  left: ReactNode;
  right: ReactNode;
  onPreset?: (preset: string) => void;
}) {
  return (
    <Frame
      title={`Split · ${preset}`}
      {...props}
      onPress={() => onPreset?.(preset === "analysis" ? "review" : "analysis")}
    >
      <box flexGrow={1} flexDirection="row">
        <box width="50%" border={["right"]}>
          {left}
        </box>
        <box flexGrow={1}>{right}</box>
      </box>
    </Frame>
  );
}
export function Overlay({ children, onClose }: { children: ReactNode; onClose?: () => void }) {
  return (
    <OverlayScrim>
      <box
        width="100%"
        height="100%"
        alignItems="center"
        justifyContent="center"
        {...(onClose ? { onMouseDown: onClose } : {})}
      >
        <box width="70%" height="50%" border>
          {children}
        </box>
      </box>
    </OverlayScrim>
  );
}
