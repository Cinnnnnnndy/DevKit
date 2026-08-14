import type { KeyEvent } from "@opentui/core";
import { useKeyboard } from "@opentui/react";
import { type ReactNode, useState } from "react";
import {
  AgentTimeline,
  ApprovalBar,
  CollapsibleOpRow,
  ContextGauge,
  DiagnosisGraph,
  DiffView,
  EvidenceList,
  HeatmapGrid,
  KnowledgeCard,
  LiveCanvas,
  MetricVisualization,
  Overlay,
  PlanCard,
  SelectorPopup,
  SideBlock,
  SortableTable,
  SplitContainer,
  SummaryCard,
  ToolCard,
  TraceView,
} from "../../components/ui/index.js";
import { colorProp } from "../../components/ui/color-props.js";
import { useUiEnvironment } from "../../components/ui/theme-context.js";

export type PatternId = `P${number}`;
const titles = [
  "Agent Timeline",
  "Plan Card",
  "Evidence",
  "Diagnosis",
  "Diff",
  "Metrics",
  "Trace",
  "Knowledge",
  "Command Palette",
  "Approval",
  "Tool Call",
  "Summary",
  "Model / Quota",
  "Index State",
  "Run Mode",
  "Side Question",
  "State-Gated Toggle",
  "Collapsible Output",
  "Permission Tier",
  "Context Gauge",
  "Live Canvas",
  "Linked Drilldown",
  "Workspace Preset",
  "Sortable Table",
  "Non-destructive Overlay",
  "AI Annotation",
] as const;
export const PATTERN_REGISTRY = Object.freeze(
  titles.map((title, index) => ({
    id: `P${String(index + 1).padStart(2, "0")}` as PatternId,
    title,
    reference: "web-feasibility-2026-08-13" as const,
  })),
);
const RATES = ["250ms", "500ms", "2s", "5s"] as const;
const PRESETS = ["F1 Migrate", "F2 Diagnose", "F3 Optimize", "F4 Observe"] as const;
export interface PatternGalleryProps {
  width: number;
  height: number;
  onExit?: () => void;
  initialSelected?: number;
  initialFrozen?: boolean;
  initialRateIndex?: number;
}
export function PatternGallery({
  width,
  height,
  onExit,
  initialSelected = 0,
  initialFrozen = false,
  initialRateIndex = 0,
}: PatternGalleryProps) {
  const { theme } = useUiEnvironment();
  const [selected, setSelected] = useState(Math.max(0, Math.min(25, initialSelected)));
  const [frozen, setFrozen] = useState(initialFrozen);
  const [rateIndex, setRateIndex] = useState(Math.max(0, Math.min(3, initialRateIndex)));
  const [linked, setLinked] = useState(0);
  const [presetIndex, setPresetIndex] = useState(0);
  const [sort, setSort] = useState<"name" | "value">("value");
  const [sortAscending, setSortAscending] = useState(false);
  const [overlay, setOverlay] = useState(false);
  const [annotation, setAnnotation] = useState(false);
  const [overlayVisits, setOverlayVisits] = useState(0);
  const current = PATTERN_REGISTRY[selected] ?? PATTERN_REGISTRY[0];
  const currentId = current?.id;
  const move = (delta: number) => setSelected((value) => (value + delta + 26) % 26);
  const activate = () => {
    if (currentId === "P21") setFrozen((v) => !v);
    else if (currentId === "P24") {
      setSort((v) => (v === "value" ? "name" : "value"));
      setSortAscending((v) => !v);
    } else if (currentId === "P25") {
      setOverlay(true);
      setOverlayVisits((v) => v + 1);
    } else if (currentId === "P26") setAnnotation((v) => !v);
  };
  const onKey = (key: KeyEvent) => {
    const name = key.name.toLowerCase();
    if (name === "escape" || name === "esc") {
      key.preventDefault();
      if (overlay) setOverlay(false);
      else onExit?.();
      return;
    }
    if (name === "down" || name === "j") {
      key.preventDefault();
      move(1);
      return;
    }
    if (name === "up" || name === "k") {
      key.preventDefault();
      move(-1);
      return;
    }
    if ((name === "left" || name === "right") && currentId === "P22") {
      key.preventDefault();
      setLinked((v) => (v + (name === "right" ? 1 : 2)) % 3);
      return;
    }
    if ((name === "left" || name === "right") && currentId === "P23") {
      key.preventDefault();
      setPresetIndex((v) => (v + (name === "right" ? 1 : 3)) % 4);
      return;
    }
    if ((name === "[" || name === "]") && currentId === "P21") {
      key.preventDefault();
      setRateIndex((v) => (v + (name === "]" ? 1 : 3)) % 4);
      return;
    }
    if (name === "enter" || name === "return" || name === "space") {
      key.preventDefault();
      activate();
    }
  };
  useKeyboard(onKey);
  const contentWidth = Math.max(
    24,
    width - Math.min(28, Math.max(18, Math.floor(width * 0.3))) - 4,
  );
  const common = { width: contentWidth, height: Math.min(12, Math.max(6, height - 7)) };
  const core = patternDemo(currentId, common, {
    frozen,
    rate: RATES[rateIndex] ?? "250ms",
    linked,
    preset: PRESETS[presetIndex] ?? PRESETS[0],
    sort,
    sortAscending,
    annotation,
    overlayVisits,
    setFrozen,
    setRateIndex,
    setPresetIndex,
    setSort,
    setAnnotation,
  });
  const sectionTitle =
    selected < 12
      ? "P01–P12 核心 Patterns"
      : selected < 20
        ? "P13–P20 已验证 Patterns"
        : "P21–P26 TUI 原生 Patterns";
  const sidebarWidth = width >= 100 ? 28 : 18;
  const showLifecycle = selected < 12 && height >= 38;
  return (
    <box
      width={width}
      height={height}
      flexDirection="row"
      focusable
      focused
      {...colorProp("backgroundColor", theme.background)}
    >
      <box
        width={sidebarWidth}
        border={["right"]}
        flexDirection="column"
        paddingX={1}
        {...colorProp("borderColor", theme.border)}
        {...colorProp("backgroundColor", theme.surface1)}
      >
        <text {...colorProp("fg", theme.primaryText)}>
          <strong>PATTERNS</strong>
        </text>
        <text {...colorProp("fg", theme.muted)}>交互模式库</text>
        <box height={1} />
        {PATTERN_REGISTRY.slice(
          Math.max(0, selected - 8),
          Math.min(26, Math.max(10, selected + 9)),
        ).map((item) => (
          <text
            key={item.id}
            wrapMode="none"
            truncate
            {...colorProp("fg", item.id === currentId ? theme.primaryText : theme.secondary)}
          >
            {item.id === currentId ? "▸" : " "} {item.id} {item.title}
          </text>
        ))}
      </box>
      <box flexGrow={1} paddingX={2} paddingTop={1} flexDirection="column" overflow="hidden">
        <text {...colorProp("fg", theme.foreground)}>
          <strong>{sectionTitle}</strong>
        </text>
        <text {...colorProp("fg", theme.muted)}>
          {selected < 12
            ? "核心闭环：理解 → 计划 → 工具执行 → 证据 → 审批 → 总结"
            : selected < 20
              ? "经过验证的状态、权限与上下文模式"
              : "面向原生终端交互的高级模式"}
        </text>
        {showLifecycle ? (
          <box
            height={8}
            marginTop={1}
            paddingX={2}
            paddingTop={1}
            flexDirection="column"
            border
            {...colorProp("borderColor", theme.borderSubtle)}
            {...colorProp("backgroundColor", theme.backgroundOuter)}
          >
            <text {...colorProp("fg", theme.secondary)}>生命周期映射：</text>
            <text {...colorProp("fg", theme.muted)}>启动 状态意图 等待执行 审查确认 收尾</text>
            <text {...colorProp("fg", theme.secondary)}>
              Env Check P02 Plan P01 Timeline P05 Diff P12 Summary
            </text>
            <text {...colorProp("fg", theme.muted)}>
              P13 Model · P14 Index · P09 Palette · P11 Tool Exec · P10 Approval · P03 Evidence
            </text>
          </box>
        ) : null}
        <box flexGrow={1} minHeight={1} marginTop={1} flexDirection="column" overflow="hidden">
          {core}
        </box>
        <text {...colorProp("fg", theme.muted)}>
          ↑↓ 选择 Pattern · ←→ 联动/预设 · Enter 操作 · Esc 返回
        </text>
      </box>
      {overlay ? (
        <Overlay>
          <box flexDirection="column">
            <text>P25 Approval Overlay</text>
            <text>Esc closes · underlying selected=P25 · visits={overlayVisits}</text>
          </box>
        </Overlay>
      ) : null}
    </box>
  );
}

type DemoState = {
  frozen: boolean;
  rate: string;
  linked: number;
  preset: string;
  sort: "name" | "value";
  sortAscending: boolean;
  annotation: boolean;
  overlayVisits: number;
  setFrozen: (fn: (v: boolean) => boolean) => void;
  setRateIndex: (fn: (v: number) => number) => void;
  setPresetIndex: (fn: (v: number) => number) => void;
  setSort: (v: "name" | "value") => void;
  setAnnotation: (fn: (v: boolean) => boolean) => void;
};
function patternDemo(
  id: PatternId | undefined,
  common: { width: number; height: number },
  state: DemoState,
): ReactNode {
  switch (id) {
    case "P01":
      return (
        <AgentTimeline
          {...common}
          height={15}
          patternId="P01"
          {...(common.width >= 70 ? { description: "所有 Agent 执行过程" } : {})}
          note={
            common.width >= 70
              ? "每步可展开工具输入/输出；失败步 ✕ danger 色并给跳转；Esc 可中断。"
              : "Enter 展开 · Esc 中断"
          }
          items={[
            { label: "Understand Request", status: "●" },
            { label: "Scan Project", status: "●", detail: "1.2s" },
            { label: "Search Knowledge Base", status: "●", detail: "3 hits" },
            { label: "Generate Migration Patch", status: "▶", detail: "⠹" },
            { label: "Compile Verify", status: "○" },
            { label: "Performance Test", status: "○" },
          ]}
        />
      );
    case "P02":
      return (
        <PlanCard
          {...common}
          height={14}
          patternId="P02"
          title="AI Plan"
          {...(common.width >= 70 ? { description: "复杂任务先出计划" } : {})}
          steps={[]}
          lines={[
            "Goal: Migrate nginx x86 project → Kunpeng ARM64",
            "1. Analyze dependency",
            "2. Find incompatible API      (knowledge_search)",
            "3. Generate patches           (code_cpp_migrator)",
            "4. Build verify   5. Benchmark",
            "Estimated: 5 tools · ~3 min",
          ]}
          actions={[
            { key: "E", label: "xecute" },
            { key: "M", label: "odify Plan" },
            { key: "C", label: "ancel" },
          ]}
        />
      );
    case "P03":
      return (
        <box flexDirection="column">
          <EvidenceList
            {...common}
            items={[
              { id: "e1", label: "Kunpeng Porting Guide §4.2", confidence: 94 },
              { id: "e2", label: "Community note", confidence: 62 },
            ]}
          />
          <text>confidence &lt;70 · Apply disabled · Enter inspect evidence</text>
        </box>
      );
    case "P04":
      return (
        <DiagnosisGraph
          {...common}
          nodes={["Build failed", "SSE intrinsic", "ARM64 yield replacement"]}
        />
      );
    case "P05":
      return (
        <DiffView
          {...common}
          lines={["@@ src/crypto.c:84 @@", "- _mm_pause();", '+ asm volatile("yield");']}
        />
      );
    case "P06":
      return (
        <MetricVisualization
          {...common}
          data={[
            { label: "QPS", value: 61, maximum: 80, unit: "k" },
            { label: "P99", value: 70, maximum: 120, unit: "ms" },
          ]}
        />
      );
    case "P07":
      return (
        <TraceView
          {...common}
          selected={1}
          lanes={[
            { label: "CPU", value: "━━ 42ms" },
            { label: "HBM", value: "━━━━ 72ms" },
            { label: "NPU", value: "━ 18ms" },
          ]}
        />
      );
    case "P08":
      return (
        <KnowledgeCard
          {...common}
          title="Knowledge Answer"
          answer="Use ARM64 yield to replace the x86 pause intrinsic."
          source="[1] Kunpeng Porting Guide §4.2"
        />
      );
    case "P09":
      return (
        <box border flexDirection="column">
          <text>COMMAND PALETTE · input: migr_</text>
          <text>RECENT /migrate nginx</text>
          <text>FILTERED ▸ Migrate current project</text>
          <text>↑↓ select · Enter run · Esc close</text>
        </box>
      );
    case "P10":
      return (
        <box flexDirection="column">
          <text>risk: medium · changes: 3 files / 21 hunks</text>
          <ApprovalBar {...common} selected="review" />
        </box>
      );
    case "P11":
      return (
        <ToolCard
          {...common}
          name="cpp_migrator"
          detail="input: nginx · running/completed · output: 21 patches · 1.2s"
          expanded
        />
      );
    case "P12":
      return (
        <SummaryCard
          {...common}
          rows={["21 issues fixed", "ARM64 build passed", "report: migration.md"]}
        />
      );
    case "P13":
      return (
        <box flexDirection="column">
          <SelectorPopup
            {...common}
            options={["qwen-72b · 62% quota", "deepseek · 18% quota", "local · unlimited"]}
            selected={0}
          />
          <text>quota resets in 03:42 · Enter select</text>
        </box>
      );
    case "P14":
      return (
        <AgentTimeline
          {...common}
          items={[
            { label: "knowledge index", status: "✓", detail: "ready" },
            { label: "codebase index", status: "▶", detail: "building 72%" },
            { label: "remote asset", status: "⚠", detail: "repair available" },
          ]}
        />
      );
    case "P15":
      return (
        <box flexDirection="column">
          <SelectorPopup
            {...common}
            options={["auto · recommended", "guided · confirmations", "manual · inspect only"]}
          />
          <text>STATUS BAR · mode:auto · model:qwen · ctx:72%</text>
        </box>
      );
    case "P16":
      return (
        <box flexDirection="column">
          <SideBlock
            {...common}
            question="Why is this API incompatible?"
            answer="AArch64 lacks the SSE intrinsic."
          />
          <text>Main task continues · answer buffered · Enter open</text>
        </box>
      );
    case "P17":
      return (
        <box border flexDirection="column">
          <text>State-Gated Toggle · migration capability OFF</text>
          <text>Install → confirm size/dependencies · Uninstall → immediate</text>
          <text>[Enter] install · [U] uninstall</text>
        </box>
      );
    case "P18":
      return (
        <box flexDirection="column">
          <CollapsibleOpRow {...common} label="READ · scan source" expanded />
          <CollapsibleOpRow {...common} label="WRITE · apply patch" />
          <text>Read expanded by default · Write collapsed by default</text>
        </box>
      );
    case "P19":
      return (
        <box border flexDirection="column">
          <text>Permission tiers</text>
          <text>L0 read ✓ · L1 local write confirm · L2 execute approval</text>
          <text>L3 network denied · secrets session-only</text>
        </box>
      );
    case "P20":
      return (
        <box flexDirection="column">
          <ContextGauge {...common} value={72} />
          <text>Fork context · Compact summary · Clear context</text>
          <text>[F] fork · [C] compact · [X] clear</text>
        </box>
      );
    case "P21":
      return (
        <LiveCanvas
          {...common}
          samples={[2, 5, 3, 8, 7, 9]}
          frozen={state.frozen}
          rate={state.rate}
          onToggleFreeze={() => state.setFrozen((v) => !v)}
          onRate={() => state.setRateIndex((v) => (v + 1) % 4)}
        />
      );
    case "P22":
      return (
        <box border flexDirection="column">
          <text>Linked selection · segment {state.linked + 1}</text>
          <text>{state.linked === 0 ? "▸" : " "} Kernel attention_fwd</text>
          <text>{state.linked === 1 ? "▸" : " "} Metric HBM 18.2ms</text>
          <text>{state.linked === 2 ? "▸" : " "} Code src/kernel.c:84</text>
          <text>←/→ links Kernel / Metric / Code</text>
        </box>
      );
    case "P23":
      return (
        <box flexDirection="column">
          <text>Workspace presets · active {state.preset}</text>
          <SplitContainer
            {...common}
            preset={state.preset}
            left={<text>Evidence</text>}
            right={<text>Diff / Metrics</text>}
            onPreset={() => state.setPresetIndex((v) => (v + 1) % 4)}
          />
          <text>F1 Migrate · F2 Diagnose · F3 Optimize · F4 Observe · ←/→</text>
        </box>
      );
    case "P24":
      return (
        <box flexDirection="column">
          <text>
            sort {state.sort} {state.sortAscending ? "↑" : "↓"}
          </text>
          <SortableTable
            {...common}
            rows={[
              { name: "attention", value: 42 },
              { name: "matmul", value: 25 },
            ]}
            sort={state.sort}
            onSort={state.setSort}
          />
        </box>
      );
    case "P25":
      return (
        <box border flexDirection="column">
          <text>Underlying workspace · selected=P25 · scroll=retained</text>
          <text>overlay visits={state.overlayVisits} · Enter open overlay</text>
        </box>
      );
    case "P26":
      return (
        <HeatmapGrid
          {...common}
          data={[{ label: "NUMA0", values: [10, 30, 70, 90] }]}
          annotation={state.annotation}
          onToggleAnnotation={() => state.setAnnotation((v) => !v)}
        />
      );
  }
  return null;
}
