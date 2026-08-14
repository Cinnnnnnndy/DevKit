import type { InputRenderable } from "@opentui/core";
import { type RefObject, useEffect, useMemo, useState } from "react";
import { colorProp } from "./color-props.js";
import { createLandingField, renderLandingField, renderLandingWave } from "./landing-field.js";
import { PromptBar } from "./prompt-bar.js";
import { useUiEnvironment } from "./theme-context.js";

const F5 = {
  A: [".###.", "#...#", "#####", "#...#", "#...#"],
  D: ["####.", "#...#", "#...#", "#...#", "####."],
  E: ["#####", "#....", "####.", "#....", "#####"],
  G: [".####", "#....", "#..##", "#...#", ".####"],
  I: ["#####", "..#..", "..#..", "..#..", "#####"],
  K: ["#...#", "#..#.", "###..", "#..#.", "#...#"],
  N: ["#...#", "##..#", "#.#.#", "#..##", "#...#"],
  P: ["####.", "#...#", "####.", "#....", "#...."],
  T: ["#####", "..#..", "..#..", "..#..", "..#.."],
  U: ["#...#", "#...#", "#...#", "#...#", ".###."],
  V: ["#...#", "#...#", "#...#", ".#.#.", "..#.."],
} as const;

type F5Character = keyof typeof F5;
function blockWord(word: string): readonly string[] {
  return Array.from({ length: 5 }, (_, row) =>
    [...word]
      .map((character) => F5[character as F5Character]?.[row] ?? ".....")
      .join(".")
      .replaceAll("#", "█")
      .replaceAll(".", " ")
      .trimEnd(),
  );
}

const KUNPENG_WORD = blockWord("KUNPENG");
const DEVKIT_WORD = blockWord("DEVKIT");
const AI_WORD = blockWord("AI");
export const LANDING_WORDMARK = Array.from({ length: 5 }, (_, row) =>
  `${KUNPENG_WORD[row] ?? ""}  ${DEVKIT_WORD[row] ?? ""}  ${AI_WORD[row] ?? ""}`.trimEnd(),
);

interface BirdRow {
  readonly lead: number;
  readonly red?: string;
  readonly gap?: number;
  readonly gray?: string;
}

export const LANDING_BIRD: readonly BirdRow[] = [
  { lead: 31, red: "▄▄" },
  { lead: 21, red: "▄▄▄███▀", gap: 1, gray: "▄█▀" },
  { lead: 15, red: "▄▄▄█████▀▀", gray: "▄▄██▀" },
  { lead: 7, red: "▄████████▀▀", gray: "▄▄█████▀" },
  { lead: 1, red: "▄▄▄▄▄▄██████▀▀", gray: "▄▄██████▀" },
  { lead: 3, red: "▀▀████▀▀", gray: "▄▄████████▀" },
  { lead: 9, gray: "▄█████████▀" },
  { lead: 11, gray: "▀▀███████▄" },
  { lead: 15, gray: "▀▀████▄" },
  { lead: 19, gray: "▀▀██▄" },
  { lead: 23, gray: "▀▀" },
] as const;

const BOOT_LOGS = [
  { time: "0.004", status: "ok", scope: "runtime", message: "本地已就绪，无需连接服务器" },
  { time: "0.011", status: "ok", scope: "toolchain", message: "交叉编译 x86_64 → Kunpeng ARM64" },
  {
    time: "0.019",
    status: "ok",
    scope: "mcp tools",
    message: "2/4 已装载  cpp_migrator · knowledge_base",
  },
  { time: "0.024", status: "warn", scope: "capabilities", message: "3 项能力未安装  [Enter] 查看" },
  {
    time: "0.031",
    status: "ok",
    scope: "session",
    message: "恢复 1 个会话  migrate nginx  3 天前 · 82% · 2 项待人工确认",
  },
] as const;

const COMPACT_MESSAGES = [
  "本地已就绪",
  "x86_64 → ARM64",
  "2/4 已装载",
  "3 项未安装",
  "恢复 migrate nginx",
] as const;

function LandingBackdrop({ width, height }: { width: number; height: number }) {
  const { theme, capabilities } = useUiEnvironment();
  const field = useMemo(() => createLandingField(width, height), [width, height]);
  const base = useMemo(() => renderLandingField(field, width, height), [field, width, height]);
  const animate = capabilities.animations !== "none" && !capabilities.ssh;
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (!animate) return undefined;
    const timer = setInterval(() => setTick((current) => current + 1), 33);
    return () => clearInterval(timer);
  }, [animate]);
  const wave = useMemo(
    () => (animate ? renderLandingWave(field, width, height, tick) : { halo: "", core: "" }),
    [animate, field, height, tick, width],
  );
  return (
    <>
      <text position="absolute" left={0} top={0} {...colorProp("fg", theme.decoration)}>
        {base}
      </text>
      {animate ? (
        <text position="absolute" left={0} top={0} {...colorProp("fg", theme.borderSubtle)}>
          {wave.halo}
        </text>
      ) : null}
      {animate ? (
        <text position="absolute" left={0} top={0} {...colorProp("fg", theme.borderStrong)}>
          {wave.core}
        </text>
      ) : null}
    </>
  );
}

function Bird() {
  const { theme } = useUiEnvironment();
  return (
    <box width={35} height={10} flexShrink={0} flexDirection="column" position="relative" left={1}>
      {LANDING_BIRD.map((row, index) => (
        <text key={`${index}-${row.lead}`} wrapMode="none">
          {" ".repeat(row.lead)}
          {row.red ? <span {...colorProp("fg", theme.kunpeng)}>{row.red}</span> : null}
          {" ".repeat(row.gap ?? 0)}
          {row.gray ? <span {...colorProp("fg", theme.kunpengSecondary)}>{row.gray}</span> : null}
        </text>
      ))}
    </box>
  );
}

function BootLogs({ compact }: { compact: boolean }) {
  const { theme } = useUiEnvironment();
  return (
    <box
      width={compact ? "100%" : 88}
      height={5}
      flexShrink={0}
      flexDirection="column"
      overflow="hidden"
    >
      {BOOT_LOGS.map((log, index) => (
        <text key={log.time} wrapMode="none" truncate {...colorProp("fg", theme.disabled)}>
          [ {log.time}]{" "}
          <span {...colorProp("fg", log.status === "ok" ? theme.success : theme.warning)}>
            {log.status.padEnd(4)}
          </span>{" "}
          <span {...colorProp("fg", theme.foreground)}>{log.scope.padEnd(compact ? 12 : 14)}</span>{" "}
          {compact ? (
            <span {...colorProp("fg", theme.secondaryOnSurface)}>{COMPACT_MESSAGES[index]}</span>
          ) : log.scope === "session" ? (
            <>
              <span {...colorProp("fg", theme.secondaryOnSurface)}>恢复 1 个会话 </span>
              <span {...colorProp("fg", theme.accent)}> migrate nginx </span>
              <span {...colorProp("fg", theme.secondaryOnSurface)}> 3 天前 · 82% · </span>
              <span {...colorProp("fg", theme.warning)}>2 项待人工确认</span>
            </>
          ) : log.scope === "capabilities" ? (
            <>
              <span {...colorProp("fg", theme.secondaryOnSurface)}>3 项能力未安装 </span>
              <span {...colorProp("fg", theme.disabled)}> [Enter] 查看</span>
            </>
          ) : (
            <span {...colorProp("fg", theme.secondaryOnSurface)}>{log.message}</span>
          )}
        </text>
      ))}
    </box>
  );
}

export function LandingScreen({
  width,
  height,
  value,
  inputRef,
  focused,
  statusMessage,
  onInput,
  onSubmit,
  onFocus,
}: {
  width: number;
  height: number;
  value: string;
  inputRef?: RefObject<InputRenderable | null>;
  focused: boolean;
  statusMessage?: string;
  onInput: (value: string) => void;
  onSubmit: (value: string) => void;
  onFocus: () => void;
}) {
  const { theme, capabilities } = useUiEnvironment();
  // 140 is the `wide-two-inspector` boundary in layoutForWidth. Keeping the
  // landing on the same boundary avoids a 140-144 band where the shell is
  // already wide but the landing is still compact.
  const compact = width < 140 || height < 38 || !capabilities.unicode;
  const contentWidth = Math.max(32, Math.min(compact ? width - 4 : 134, width - 4));
  const promptWidth = Math.max(32, Math.min(94, contentWidth));
  return (
    <box
      id="landing"
      width="100%"
      height="100%"
      {...colorProp("backgroundColor", theme.background)}
      alignItems="center"
      justifyContent="center"
      overflow="hidden"
    >
      <LandingBackdrop width={width} height={height} />
      <box width={contentWidth} flexDirection="column" alignItems="center">
        {compact ? (
          <box height={2} flexShrink={0} flexDirection="column" alignItems="center">
            <text {...colorProp("fg", theme.foreground)}>
              <span {...colorProp("fg", theme.kunpeng)}>◢</span> KUNPENG DEVKIT AI
            </text>
            <text {...colorProp("fg", theme.kunpengSecondary)}>KUNPENG · NATIVE AI TERMINAL</text>
          </box>
        ) : (
          <box
            height={10}
            flexShrink={0}
            flexDirection="row"
            alignItems="center"
            justifyContent="center"
            position="relative"
            left={-5}
          >
            <Bird />
            <box width={91} height={5} flexShrink={0} flexDirection="column" marginLeft={2}>
              {LANDING_WORDMARK.map((line, index) => (
                <text
                  key={`${index}-${line}`}
                  wrapMode="none"
                  {...colorProp("fg", theme.foreground)}
                >
                  <strong>{line}</strong>
                </text>
              ))}
            </box>
          </box>
        )}
        <box height={1} flexShrink={0} marginBottom={1} flexDirection="row" gap={1}>
          {(["AI TERMINAL", "NATIVE TUI", "v26.0", "KUNPENG ARM64"] as const).map((chip) => (
            <text
              key={chip}
              {...colorProp("fg", theme.foreground)}
              {...colorProp("bg", theme.surface4)}
            >
              {" "}
              {chip}{" "}
            </text>
          ))}
        </box>
        <BootLogs compact={compact} />
        <box
          width={promptWidth}
          height={3}
          flexShrink={0}
          marginTop={1}
          position="relative"
          left={compact ? 0 : -4}
        >
          <PromptBar
            value={value}
            focused={focused}
            {...(inputRef ? { inputRef } : {})}
            placeholder=" 想做什么？直接说 —— 例如「把 ./nginx 迁到鲲鹏」"
            shortcutLabel={compact ? "" : "Ctrl+P 命令面板"}
            onInput={onInput}
            onSubmit={onSubmit}
            onFocus={onFocus}
          />
        </box>
        <box height={1} flexShrink={0} marginTop={1} flexDirection="row" gap={1}>
          <text {...colorProp("fg", theme.disabled)}>建议</text>
          <text {...colorProp("fg", theme.secondaryOnSurface)} {...colorProp("bg", theme.surface2)}>
            {" "}
            安装迁移能力包{" "}
          </text>
          <text {...colorProp("fg", theme.muted)} {...colorProp("bg", theme.surface1)}>
            {" "}
            扫描当前工程{" "}
          </text>
          <text {...colorProp("fg", theme.muted)} {...colorProp("bg", theme.surface1)}>
            {" "}
            继续上次任务{" "}
          </text>
        </box>
        {statusMessage ? (
          <text {...colorProp("fg", statusMessage.includes("failed") ? theme.danger : theme.muted)}>
            {statusMessage}
          </text>
        ) : null}
      </box>
    </box>
  );
}
