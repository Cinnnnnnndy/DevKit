import type { ReactNode } from "react";
import { ActionButton, Panel, SectionLabel, useUiEnvironment } from "../../components/ui";
import { colorProp } from "../../components/ui/color-props.js";
import type { ConfigurationRequirement, MigrationPatch, PlanStepStatus } from "../../domain";
import type { MigrationFlowActions, MigrationFlowState } from "./types";
export interface MigrationActPresenterProps {
  readonly state: MigrationFlowState;
  readonly actions: MigrationFlowActions;
  readonly width: number;
  readonly height: number;
}
function statusSymbol(status: PlanStepStatus): string {
  switch (status) {
    case "completed":
      return "✓";
    case "running":
      return "▶";
    case "paused":
      return "⏸";
    case "failed":
      return "✕";
    case "skipped":
      return "–";
    case "pending":
      return "○";
  }
}
function FlowPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Panel title={title} focused>
      {children}
    </Panel>
  );
}
function FlowFeedback({ state, actions }: Pick<MigrationActPresenterProps, "state" | "actions">) {
  const { theme } = useUiEnvironment();
  if (state.asyncStatus === "loading") {
    return (
      <box height={2} flexShrink={0} paddingX={1} {...colorProp("backgroundColor", theme.surface2)}>
        <text {...colorProp("fg", theme.primaryText)}>▶ {state.pendingOperation ?? "处理中"}</text>
        <text {...colorProp("fg", theme.muted)}>Esc 可取消</text>
      </box>
    );
  }
  if (state.asyncStatus === "error" && state.error !== undefined) {
    return (
      <box height={3} flexShrink={0} paddingX={1} {...colorProp("backgroundColor", theme.surface2)}>
        <text {...colorProp("fg", theme.danger)}>✕ {state.error.message}</text>
        <box height={1} flexShrink={0} flexDirection="row" gap={1}>
          {state.error.retryable ? (
            // biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI text supports mouse input; R is the keyboard equivalent.
            <text {...colorProp("fg", theme.primaryText)} onMouseDown={() => void actions.retry()}>
              [R] 重试
            </text>
          ) : null}
          {/* biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI text supports mouse input; Esc is the keyboard equivalent. */}
          <text {...colorProp("fg", theme.secondary)} onMouseDown={() => actions.clearError()}>
            [Esc] 返回
          </text>
        </box>
      </box>
    );
  }
  if (state.asyncStatus === "cancelled") {
    return (
      <box height={2} flexShrink={0} paddingX={1} {...colorProp("backgroundColor", theme.surface2)}>
        <text {...colorProp("fg", theme.warning)}>⚠ 操作已取消，当前数据保持不变</text>
        {/* biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI text supports mouse input; R is the keyboard equivalent. */}
        <text {...colorProp("fg", theme.primaryText)} onMouseDown={() => void actions.retry()}>
          [R] 重新执行
        </text>
      </box>
    );
  }
  if (state.asyncStatus === "empty") {
    return (
      <box height={1} flexShrink={0} paddingX={1}>
        <text {...colorProp("fg", theme.muted)}>○ 当前场景没有可展示数据</text>
      </box>
    );
  }
  return null;
}
function defaultConfigurationValues(
  configuration: ConfigurationRequirement,
): Readonly<Record<string, string | number>> {
  const entries: Array<[string, string | number]> = [];
  for (const field of configuration.fields) {
    if (field.defaultValue !== undefined) entries.push([field.key, field.defaultValue]);
  }
  return Object.fromEntries(entries);
}
export function LandingActPresenter(props: MigrationActPresenterProps) {
  const { state, actions, width } = props;
  const { theme } = useUiEnvironment();
  const workspace = state.workspace;
  const visibleCapabilities = workspace?.capabilities.slice(0, width < 80 ? 3 : 6) ?? [];
  return (
    <FlowPanel title="ACT 01 · ZERO-CONFIG LANDING">
      <FlowFeedback state={state} actions={actions} />
      <text {...colorProp("fg", theme.foreground)}>
        <strong>KUNPENG DEVKIT AI</strong> · native terminal engineering workspace
      </text>
      <text {...colorProp("fg", theme.secondary)}>
        {workspace?.runtimeReady ? "✓ Runtime 本地已就绪" : "○ 正在检查 Runtime"} · x86_64 → ARM64
      </text>
      <box height={1} flexShrink={0} marginTop={1}>
        <SectionLabel count={visibleCapabilities.length}>CAPABILITIES</SectionLabel>
      </box>
      {visibleCapabilities.map((capability) => (
        <text key={capability.id} {...colorProp("fg", theme.foreground)} wrapMode="none" truncate>
          <span
            {...colorProp(
              "fg",
              capability.status === "ready"
                ? theme.success
                : capability.status === "blocked"
                  ? theme.warning
                  : theme.secondary,
            )}
          >
            {capability.status === "ready" ? "✓" : capability.status === "blocked" ? "⚠" : "○"}
          </span>{" "}
          {capability.name} <span {...colorProp("fg", theme.muted)}>{capability.description}</span>
        </text>
      ))}
      <box flexGrow={1} minHeight={1} />
      <text {...colorProp("fg", theme.muted)}>INTENT</text>
      <text {...colorProp("fg", theme.foreground)} wrapMode="none" truncate>
        ❯ {state.intent.prompt}
      </text>
      <text {...colorProp("fg", theme.accent)}>{state.intent.sourcePath}</text>
      <box height={3} flexShrink={0} marginTop={1}>
        <ActionButton
          label="Enter 生成迁移计划"
          active
          disabled={state.asyncStatus === "loading"}
          onPress={() => void actions.submitIntent()}
        />
      </box>
    </FlowPanel>
  );
}
export function PlanActPresenter({ state, actions, width }: MigrationActPresenterProps) {
  const { theme } = useUiEnvironment();
  const plan = state.plan;
  const visibleSteps = plan?.steps.slice(0, width < 80 ? 4 : 8) ?? [];
  return (
    <FlowPanel title="ACT 02 · EDITABLE AI PLAN">
      <FlowFeedback state={state} actions={actions} />
      <text {...colorProp("fg", theme.foreground)} wrapMode="none" truncate>
        <strong>Goal</strong> {plan?.goal ?? "等待生成计划"}
      </text>
      <text {...colorProp("fg", theme.secondary)}>
        {plan === undefined
          ? ""
          : `v${plan.version} · ${plan.steps.length} steps · ~${Math.ceil(plan.estimatedDurationMs / 60000)} min`}
      </text>
      <box height={1} flexShrink={0} marginTop={1}>
        <SectionLabel>PLAN STEPS</SectionLabel>
      </box>
      {visibleSteps.map((step, index) => (
        <text key={step.id} {...colorProp("fg", theme.foreground)} wrapMode="none" truncate>
          <span {...colorProp("fg", step.status === "failed" ? theme.danger : theme.secondary)}>
            {statusSymbol(step.status)} {String(index + 1).padStart(2, "0")}
          </span>{" "}
          {step.title}{" "}
          {width < 80 || step.tool === undefined ? null : (
            <span {...colorProp("fg", theme.accent)}>({step.tool})</span>
          )}
        </text>
      ))}
      <box flexGrow={1} minHeight={1} />
      <text {...colorProp("fg", theme.muted)}>M 修改步骤 · Enter 执行 · Esc 返回</text>
      <box height={3} flexShrink={0} flexDirection="row">
        <ActionButton
          label="Execute Plan"
          active
          disabled={
            plan === undefined || plan.steps.length === 0 || state.asyncStatus === "loading"
          }
          onPress={() => void actions.executePlan()}
        />
      </box>
    </FlowPanel>
  );
}
export function ConfigActPresenter({ state, actions }: MigrationActPresenterProps) {
  const { theme } = useUiEnvironment();
  const configuration = state.configuration;
  return (
    <FlowPanel title="ACT 03 · CONFIG COMPLETION">
      <FlowFeedback state={state} actions={actions} />
      <text {...colorProp("fg", theme.warning)}>⏸ Build verify 暂停</text>
      <text {...colorProp("fg", theme.secondary)} wrapMode="word">
        {configuration?.reason ?? "等待配置要求"}
      </text>
      <box height={1} flexShrink={0} marginTop={1}>
        <SectionLabel>REQUIRED AT THIS STEP</SectionLabel>
      </box>
      {configuration?.fields.map((field, index) => (
        <box
          key={field.key}
          height={2}
          flexShrink={0}
          {...(index === 0 ? { border: ["left"] as const } : {})}
          {...(index === 0 ? colorProp("borderColor", theme.borderStrong) : {})}
          {...colorProp("backgroundColor", index === 0 ? theme.focus : theme.background)}
          paddingX={1}
          flexDirection="row"
        >
          <text width={18} {...colorProp("fg", theme.muted)} wrapMode="none" truncate>
            {index === 0 ? "▎" : " "}
            {field.label}
          </text>
          <text flexGrow={1} {...colorProp("fg", theme.foreground)} wrapMode="none" truncate>
            {field.sensitive ? "••••••••" : String(field.defaultValue ?? "")}
          </text>
        </box>
      ))}
      <box flexGrow={1} minHeight={1} />
      <text {...colorProp("fg", theme.muted)}>非敏感项仅保存在当前 Mock 会话 · Esc 可中止</text>
      <box height={3} flexShrink={0} flexDirection="row">
        <ActionButton
          label="Enter 填完继续"
          active
          disabled={configuration === undefined || state.asyncStatus === "loading"}
          onPress={() =>
            configuration === undefined
              ? undefined
              : void actions.submitConfiguration(defaultConfigurationValues(configuration))
          }
        />
        <ActionButton
          label="S 跳过验证"
          disabled={!configuration?.canSkip}
          onPress={() => void actions.submitConfiguration({}, true)}
        />
      </box>
    </FlowPanel>
  );
}
export function ReportActPresenter({ state, actions, width }: MigrationActPresenterProps) {
  const { theme, capabilities } = useUiEnvironment();
  const report = state.report;
  const fill = capabilities.unicode ? "█" : "#";
  const empty = capabilities.unicode ? "░" : ".";
  const visibleFiles = report?.files.slice(0, width < 80 ? 5 : 10) ?? [];
  const compatibilityScore = Number.isFinite(report?.compatibilityScore)
    ? Math.max(0, Math.min(100, report?.compatibilityScore ?? 0))
    : 0;
  const compatibilityCells = Math.round(compatibilityScore / 10);
  return (
    <FlowPanel title="ACT 04 · COMPATIBILITY REPORT">
      <FlowFeedback state={state} actions={actions} />
      <text {...colorProp("fg", theme.foreground)}>
        <strong>Compatibility</strong>{" "}
        <span {...colorProp("fg", theme.secondary)}>
          {fill.repeat(compatibilityCells)}
          {empty.repeat(10 - compatibilityCells)} {compatibilityScore}%
        </span>
      </text>
      <text {...colorProp("fg", theme.secondary)}>
        Critical <span {...colorProp("fg", theme.danger)}>{report?.criticalCount ?? 0}</span> ·
        Warning <span {...colorProp("fg", theme.warning)}>{report?.warningCount ?? 0}</span> ·
        Auto-fix <span {...colorProp("fg", theme.success)}>{report?.autoFixableCount ?? 0}</span>
      </text>
      <box height={1} flexShrink={0} marginTop={1}>
        <SectionLabel count={report?.files.length ?? 0}>FILE RISK HEATMAP</SectionLabel>
      </box>
      {visibleFiles.map((file) => {
        const risk = Number.isFinite(file.risk) ? Math.max(0, Math.min(1, file.risk)) : 0;
        const intensity = Math.min(3, Math.floor(risk * 4));
        const riskGlyph = capabilities.unicode ? (["░", "▒", "▓", "█"][intensity] ?? "░") : "#";
        const riskColor =
          intensity >= 3 ? theme.foreground : intensity >= 1 ? theme.secondary : theme.muted;
        return (
          // biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI rows are mouse-selectable and expose arrow-key selection through the controller.
          <text
            key={file.path}
            {...colorProp(
              "fg",
              state.selectedRiskFile?.path === file.path ? theme.foreground : theme.secondary,
            )}
            wrapMode="none"
            truncate
            onMouseDown={() => actions.selectRiskFile(file.path)}
          >
            {state.selectedRiskFile?.path === file.path ? "▎" : " "}
            <span {...colorProp("fg", riskColor)}>
              {riskGlyph.repeat(Math.max(1, Math.round(risk * 12)))}
            </span>{" "}
            {file.path} <span {...colorProp("fg", theme.muted)}>{file.issueCount} issues</span>
          </text>
        );
      })}
      <box flexGrow={1} minHeight={1} />
      <box height={3} flexShrink={0}>
        <ActionButton
          label="Enter 审查迁移补丁"
          active
          disabled={state.asyncStatus === "loading"}
          onPress={() => void actions.openPatchReview()}
        />
      </box>
    </FlowPanel>
  );
}
function PatchDiff({ patch }: { patch: MigrationPatch }) {
  const { theme } = useUiEnvironment();
  return (
    <>
      <text {...colorProp("fg", theme.accent)} wrapMode="none" truncate>
        {patch.file} · {patch.summary}
      </text>
      {patch.lines.slice(0, 8).map((line, index) => (
        <text
          key={`${line.kind}-${line.oldLine ?? ""}-${line.newLine ?? ""}-${index}`}
          {...colorProp(
            "fg",
            line.kind === "addition"
              ? theme.success
              : line.kind === "deletion"
                ? theme.danger
                : theme.secondary,
          )}
          wrapMode="none"
          truncate
        >
          {line.kind === "addition" ? "+" : line.kind === "deletion" ? "-" : " "} {line.content}
        </text>
      ))}
      <box height={1} flexShrink={0} marginTop={1}>
        <SectionLabel count={patch.evidence.length}>EVIDENCE</SectionLabel>
      </box>
      {patch.evidence.slice(0, 3).map((evidence, index) => (
        <text key={evidence.id} {...colorProp("fg", theme.foreground)} wrapMode="none" truncate>
          [{index + 1}] {evidence.label}{" "}
          <span {...colorProp("fg", theme.accent)}>{evidence.locator}</span>
        </text>
      ))}
    </>
  );
}
export function PatchReviewActPresenter({ state, actions }: MigrationActPresenterProps) {
  const { theme } = useUiEnvironment();
  const review = state.patchReview;
  const selected = review?.patches[state.selectedPatchIndex];
  return (
    <FlowPanel title="ACT 05 · PATCH & EVIDENCE REVIEW">
      <FlowFeedback state={state} actions={actions} />
      <text {...colorProp("fg", theme.secondary)}>
        {review === undefined
          ? "等待补丁"
          : `${state.selectedPatchIndex + 1}/${review.patches.length} · ${review.acceptedCount} accepted · ${review.rejectedCount} rejected · ${review.pendingCount} pending`}
      </text>
      {selected === undefined ? (
        <box flexGrow={1} alignItems="center" justifyContent="center">
          <text {...colorProp("fg", theme.muted)}>No patch data</text>
        </box>
      ) : (
        <PatchDiff patch={selected} />
      )}
      <box flexGrow={1} minHeight={1} />
      <box height={3} flexShrink={0} flexDirection="row">
        <ActionButton
          label="A Accept"
          active
          disabled={selected === undefined || state.asyncStatus === "loading"}
          onPress={() =>
            selected === undefined ? undefined : void actions.reviewPatch(selected.id, "accepted")
          }
        />
        <ActionButton
          label="R Reject"
          danger
          disabled={selected === undefined || state.asyncStatus === "loading"}
          onPress={() =>
            selected === undefined ? undefined : void actions.reviewPatch(selected.id, "rejected")
          }
        />
        <ActionButton
          label="Build Verify"
          disabled={(review?.pendingCount ?? 0) > 0 || state.asyncStatus === "loading"}
          onPress={() => void actions.runInitialBuild()}
        />
      </box>
    </FlowPanel>
  );
}
export function BuildDiagnosisActPresenter({ state, actions }: MigrationActPresenterProps) {
  const { theme, capabilities } = useUiEnvironment();
  const build = state.build;
  const diagnosis = state.diagnosis;
  const confidence = Number.isFinite(diagnosis?.confidence)
    ? Math.max(0, Math.min(1, diagnosis?.confidence ?? 0))
    : 0;
  const confidenceCells = Math.round(confidence * 10);
  const fill = capabilities.unicode ? "█" : "#";
  const empty = capabilities.unicode ? "░" : ".";
  return (
    <FlowPanel title="ACT 06 · BUILD FAILURE → DIAGNOSE → VERIFY">
      <FlowFeedback state={state} actions={actions} />
      <text {...colorProp("fg", build?.status === "passed" ? theme.success : theme.danger)}>
        {build?.status === "passed" ? "✓ BUILD PASS" : "✕ BUILD FAILED"}{" "}
        <span {...colorProp("fg", theme.muted)}>{build?.durationMs ?? 0} ms</span>
      </text>
      <text {...colorProp("fg", theme.secondary)} wrapMode="none" truncate>
        {build?.command ?? "等待构建"}
      </text>
      {state.phase === "build-failed" ? (
        <>
          <text {...colorProp("fg", theme.danger)}>{build?.failure?.message ?? "构建失败"}</text>
          {build?.output.slice(-3).map((line, index) => (
            <text
              key={`${index}-${line}`}
              {...colorProp("fg", theme.muted)}
              wrapMode="none"
              truncate
            >
              {line}
            </text>
          ))}
        </>
      ) : null}
      {state.phase === "diagnosis" && diagnosis !== undefined ? (
        <>
          <box height={1} flexShrink={0} marginTop={1}>
            <SectionLabel>ROOT CAUSE</SectionLabel>
          </box>
          <text {...colorProp("fg", theme.foreground)}>▎ {diagnosis.rootCause}</text>
          <text {...colorProp("fg", theme.secondary)}>
            Confidence{" "}
            <span {...colorProp("fg", theme.accent)}>
              {fill.repeat(confidenceCells)}
              {empty.repeat(10 - confidenceCells)} {Math.round(confidence * 100)}%
            </span>
          </text>
          {diagnosis.evidence.slice(0, 4).map((evidence, index) => (
            <text key={evidence.id} {...colorProp("fg", theme.foreground)} wrapMode="none" truncate>
              [{index + 1}] {evidence.label}{" "}
              <span {...colorProp("fg", theme.accent)}>{evidence.locator}</span>
            </text>
          ))}
          <text {...colorProp("fg", theme.secondary)}>Fix: {diagnosis.proposedFixSummary}</text>
        </>
      ) : null}
      <box flexGrow={1} minHeight={1} />
      <box height={3} flexShrink={0}>
        {state.phase === "build-failed" ? (
          <ActionButton
            label="Enter 分析根因"
            active
            onPress={() => void actions.diagnoseBuild()}
          />
        ) : state.phase === "diagnosis" ? (
          <ActionButton
            label={
              (diagnosis?.confidence ?? 0) < 0.7 ? "Review Fix（低置信度）" : "Apply Fix & Rebuild"
            }
            active={(diagnosis?.confidence ?? 0) >= 0.7}
            disabled={(diagnosis?.confidence ?? 0) < 0.7}
            onPress={() => void actions.applyFixAndRetryBuild()}
          />
        ) : (
          <ActionButton
            label="Run Performance Baseline"
            active
            onPress={() => void actions.collectBaseline()}
          />
        )}
      </box>
    </FlowPanel>
  );
}
export function BaselineActPresenter({ state, actions, width }: MigrationActPresenterProps) {
  const { theme, capabilities } = useUiEnvironment();
  const baseline = state.baseline;
  const fill = capabilities.unicode ? "█" : "#";
  return (
    <FlowPanel title="ACT 07 · PERFORMANCE BASELINE">
      <FlowFeedback state={state} actions={actions} />
      <text {...colorProp("fg", theme.foreground)}>
        QPS <strong>{baseline?.metrics.qps.toLocaleString() ?? "—"}</strong> · P99{" "}
        <strong>{baseline?.metrics.p99LatencyMs ?? "—"} ms</strong>
      </text>
      <text {...colorProp("fg", theme.warning)}>
        AI finding · {baseline?.bottleneck ?? "waiting"}
      </text>
      <box height={1} flexShrink={0} marginTop={1}>
        <SectionLabel>TRACE LANES</SectionLabel>
      </box>
      {baseline?.trace.map((lane, laneIndex) => (
        <text key={lane.id} {...colorProp("fg", theme.secondary)} wrapMode="none" truncate>
          {lane.label.padEnd(10)}{" "}
          {lane.spans.map((span) => (
            <span
              key={span.id}
              {...colorProp(
                "fg",
                (laneIndex === 0 ? theme.cpu[2] : theme.memory[2]) ?? theme.secondary,
              )}
            >
              {fill.repeat(
                Math.max(1, Math.min(Math.max(4, width - 20), Math.round(span.durationMs / 5))),
              )}
            </span>
          ))}
        </text>
      ))}
      <text {...colorProp("fg", theme.secondary)}>
        HBM{" "}
        <span {...colorProp("fg", theme.memory[3] ?? theme.secondary)}>
          {baseline?.hbmUtilizationPercent ?? 0}%
        </span>{" "}
        · NPU{" "}
        <span {...colorProp("fg", theme.npu[2] ?? theme.secondary)}>
          {baseline?.npuUtilizationPercent ?? 0}%
        </span>
      </text>
      <box flexGrow={1} minHeight={1} />
      <box height={3} flexShrink={0}>
        <ActionButton
          label="Enter 比较调优方案"
          active
          onPress={() => void actions.compareTuningPlans()}
        />
      </box>
    </FlowPanel>
  );
}
export function TuningActPresenter({ state, actions, width }: MigrationActPresenterProps) {
  const { theme } = useUiEnvironment();
  const plans = state.tuning?.plans.slice(0, width < 80 ? 2 : 4) ?? [];
  const recommended = plans.find((plan) => plan.recommended);
  return (
    <FlowPanel title="ACT 08 · TUNING PLAN COMPARISON">
      <FlowFeedback state={state} actions={actions} />
      <box height={1} flexShrink={0}>
        <SectionLabel count={plans.length}>PLAN · QPS · P99 · CPU · MEMORY</SectionLabel>
      </box>
      {plans.map((plan) => (
        // biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI rows are mouse-selectable and have keyboard action equivalents.
        <box
          key={plan.id}
          height={3}
          flexShrink={0}
          {...(plan.recommended ? { border: ["left"] as const } : {})}
          {...(plan.recommended ? colorProp("borderColor", theme.borderStrong) : {})}
          {...colorProp("backgroundColor", plan.recommended ? theme.focus : theme.background)}
          paddingX={1}
          flexDirection="column"
          onMouseDown={() => void actions.applyTuningPlan(plan.id)}
        >
          <text {...colorProp("fg", theme.foreground)} wrapMode="none" truncate>
            {plan.recommended ? "▎" : " "}
            {plan.name} {plan.recommended ? "★ 推荐" : ""} · {plan.metrics.qps.toLocaleString()} ·{" "}
            {plan.metrics.p99LatencyMs}ms · {plan.metrics.cpuPercent}% · {plan.metrics.memoryGiB}GiB
          </text>
          <text {...colorProp("fg", theme.muted)} wrapMode="none" truncate>
            {plan.description} · {plan.tradeoffs.join(" · ")}
          </text>
        </box>
      ))}
      {state.tuningApplication === undefined ? null : (
        <text {...colorProp("fg", theme.success)}>
          ✓ Applied {state.tuningApplication.planId} · QPS{" "}
          {state.tuningApplication.before.qps.toLocaleString()} →{" "}
          {state.tuningApplication.after.qps.toLocaleString()}
        </text>
      )}
      <box flexGrow={1} minHeight={1} />
      <box height={3} flexShrink={0} flexDirection="row">
        <ActionButton
          label="Apply Recommended"
          active
          disabled={recommended === undefined || state.asyncStatus === "loading"}
          onPress={() =>
            recommended === undefined ? undefined : void actions.applyTuningPlan(recommended.id)
          }
        />
        <ActionButton
          label="Next: Scenario Profile"
          disabled={state.tuningApplication === undefined}
          onPress={() => void actions.openProfiles()}
        />
      </box>
    </FlowPanel>
  );
}
export function ProfileActPresenter({ state, actions }: MigrationActPresenterProps) {
  const { theme } = useUiEnvironment();
  return (
    <FlowPanel title="ACT 09 · SCENARIO PROFILE">
      <FlowFeedback state={state} actions={actions} />
      <box height={1} flexShrink={0}>
        <SectionLabel count={state.profiles?.length ?? 0}>WORKLOAD PROFILES</SectionLabel>
      </box>
      {state.profiles?.map((profile) => {
        const selected = profile.id === state.selectedProfileId;
        return (
          // biome-ignore lint/a11y/noStaticElementInteractions: OpenTUI rows are mouse-selectable and have arrow-key equivalents.
          <box
            key={profile.id}
            height={3}
            flexShrink={0}
            {...(selected ? { border: ["left"] as const } : {})}
            {...(selected ? colorProp("borderColor", theme.borderStrong) : {})}
            {...colorProp("backgroundColor", selected ? theme.focus : theme.background)}
            paddingX={1}
            flexDirection="column"
            onMouseDown={() => actions.selectProfile(profile.id)}
          >
            <text
              {...colorProp("fg", selected ? theme.foreground : theme.secondary)}
              wrapMode="none"
              truncate
            >
              {selected ? "▎" : " "}
              {profile.name} · ~{Math.ceil(profile.estimatedDurationMs / 1000)}s
            </text>
            <text {...colorProp("fg", theme.muted)} wrapMode="none" truncate>
              {profile.description}
            </text>
          </box>
        );
      })}
      {state.profileResult === undefined ? null : (
        <text
          {...colorProp(
            "fg",
            state.profileResult.status === "passed" ? theme.success : theme.warning,
          )}
        >
          {state.profileResult.status === "passed" ? "✓" : "⚠"}{" "}
          {state.profileResult.observations.join(" · ")}
        </text>
      )}
      <box flexGrow={1} minHeight={1} />
      <box height={3} flexShrink={0} flexDirection="row">
        <ActionButton
          label="Run Selected Profile"
          active
          disabled={state.selectedProfileId === undefined || state.asyncStatus === "loading"}
          onPress={() => void actions.runSelectedProfile()}
        />
        <ActionButton
          label="Session Summary"
          disabled={state.profileResult === undefined}
          onPress={() => void actions.finishSession()}
        />
      </box>
    </FlowPanel>
  );
}
export function SummaryActPresenter({ state, actions, width, height }: MigrationActPresenterProps) {
  const { theme } = useUiEnvironment();
  const summary = state.summary;
  const compact = width < 80 || height < 22;
  const visibleFiles = summary?.modifiedFiles.slice(0, compact ? 3 : 6) ?? [];
  const gain =
    summary === undefined || summary.baseline.qps === 0
      ? 0
      : Math.round(
          ((summary.finalMetrics.qps - summary.baseline.qps) / summary.baseline.qps) * 100,
        );
  return (
    <FlowPanel title="ACT 10 · SESSION SUMMARY">
      <FlowFeedback state={state} actions={actions} />
      <text
        height={1}
        flexShrink={0}
        {...colorProp("fg", theme.foreground)}
        wrapMode="none"
        truncate
      >
        <strong>{summary?.title ?? "Session Summary"}</strong>
      </text>
      {compact ? (
        <text
          height={1}
          flexShrink={0}
          {...colorProp("fg", theme.secondary)}
          wrapMode="none"
          truncate
        >
          <span {...colorProp("fg", theme.success)}>✓ {summary?.fixedIssueCount ?? 0} fixed</span> ·{" "}
          <span {...colorProp("fg", theme.warning)}>
            ⚠ {summary?.manualReviewCount ?? 0} manual
          </span>{" "}
          ·{" "}
          <span
            {...colorProp("fg", summary?.buildStatus === "passed" ? theme.success : theme.danger)}
          >
            Build {summary?.buildStatus.toUpperCase() ?? "—"}
          </span>
        </text>
      ) : (
        <>
          <text height={1} flexShrink={0} {...colorProp("fg", theme.success)}>
            ✓ {summary?.fixedIssueCount ?? 0} issues fixed
          </text>
          <text height={1} flexShrink={0} {...colorProp("fg", theme.warning)}>
            ⚠ {summary?.manualReviewCount ?? 0} need manual review
          </text>
          <text
            height={1}
            flexShrink={0}
            {...colorProp("fg", summary?.buildStatus === "passed" ? theme.success : theme.danger)}
          >
            Build {summary?.buildStatus.toUpperCase() ?? "—"}
          </text>
        </>
      )}
      <box height={1} flexShrink={0} marginTop={compact ? 0 : 1}>
        <SectionLabel>PERFORMANCE</SectionLabel>
      </box>
      {compact ? (
        <text
          height={1}
          flexShrink={0}
          {...colorProp("fg", theme.foreground)}
          wrapMode="none"
          truncate
        >
          QPS {summary?.baseline.qps.toLocaleString() ?? "—"} →{" "}
          {summary?.finalMetrics.qps.toLocaleString() ?? "—"}{" "}
          <span {...colorProp("fg", theme.success)}>+{gain}%</span> · P99{" "}
          {summary?.baseline.p99LatencyMs ?? "—"}ms → {summary?.finalMetrics.p99LatencyMs ?? "—"}ms
        </text>
      ) : (
        <>
          <text height={1} flexShrink={0} {...colorProp("fg", theme.foreground)}>
            QPS {summary?.baseline.qps.toLocaleString() ?? "—"} →{" "}
            {summary?.finalMetrics.qps.toLocaleString() ?? "—"}{" "}
            <span {...colorProp("fg", theme.success)}>+{gain}%</span>
          </text>
          <text height={1} flexShrink={0} {...colorProp("fg", theme.secondary)}>
            P99 {summary?.baseline.p99LatencyMs ?? "—"}ms →{" "}
            {summary?.finalMetrics.p99LatencyMs ?? "—"}ms
          </text>
        </>
      )}
      <box height={1} flexShrink={0} marginTop={compact ? 0 : 1}>
        <SectionLabel count={summary?.modifiedFiles.length ?? 0}>MODIFIED FILES</SectionLabel>
      </box>
      {visibleFiles.map((file) => (
        <text
          key={file}
          height={1}
          flexShrink={0}
          {...colorProp("fg", theme.secondary)}
          wrapMode="none"
          truncate
        >
          · {file}
        </text>
      ))}
      <box flexGrow={1} minHeight={compact ? 0 : 1} />
      {state.exportedReport === undefined ? null : (
        <text
          height={1}
          flexShrink={0}
          {...colorProp("fg", theme.success)}
          wrapMode="none"
          truncate
        >
          ✓ Report saved: {state.exportedReport.destinationPath}
        </text>
      )}
      <box height={3} flexShrink={0} flexDirection="row">
        <ActionButton
          label="S Export Markdown"
          active
          disabled={summary === undefined || state.asyncStatus === "loading"}
          onPress={() => void actions.exportSummary("markdown", "reports/nginx-migration.md")}
        />
        <ActionButton
          label="J Export JSON"
          disabled={summary === undefined || state.asyncStatus === "loading"}
          onPress={() => void actions.exportSummary("json", "reports/nginx-migration.json")}
        />
      </box>
    </FlowPanel>
  );
}
