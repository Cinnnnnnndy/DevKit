import type { ReactNode } from "react";
import { capabilityColor, colorProp, fitChartText } from "./chart-primitives.js";
import { resolveChartPalette } from "./palette.js";
import type { ChartBaseProps } from "./types.js";

export type ChartLegendItem = {
  label: string;
  color?: string | undefined;
  marker?: string | undefined;
};
export type ChartAxis = { minimum: string; maximum: string; midpoint?: string };
export type ChartFrameLayout = { width: number; height: number };
export type ChartFrameProps = ChartBaseProps & {
  title: string;
  legend?: readonly ChartLegendItem[];
  xAxis?: ChartAxis;
  yAxis?: ChartAxis;
  borderless?: boolean;
  frameStyle?: "boxed" | "open";
  children?: ReactNode | ((layout: ChartFrameLayout) => ReactNode);
};

/** Shared neutral chart chrome. It owns only framing, legend and axes; callers own data rendering. */
export function ChartFrame({
  width,
  height,
  palette,
  capabilities,
  title,
  legend = [],
  xAxis,
  yAxis,
  borderless = false,
  frameStyle = "boxed",
  children,
}: ChartFrameProps) {
  const colors = resolveChartPalette(palette, capabilities);
  const caps = { colorMode: "truecolor" as const, braille: true, unicode: true, ...capabilities };
  const safeWidth = Math.max(1, Math.floor(width));
  const safeHeight = Math.max(1, Math.floor(height));
  if (safeWidth < 4 || safeHeight < 2)
    return (
      <box width={safeWidth} height={safeHeight} overflow="hidden">
        <text wrapMode="none" truncate {...colorProp("fg", capabilityColor(colors.text, caps))}>
          {fitChartText(title, safeWidth)}
        </text>
      </box>
    );
  const frameInset = borderless ? 0 : 2;
  const titleRows = borderless ? 1 : 0;
  const legendRows = legend.length ? 1 : 0;
  const xRows = xAxis ? 1 : 0;
  const yWidth = yAxis
    ? Math.min(
        8,
        Math.max(yAxis.minimum.length, yAxis.maximum.length, yAxis.midpoint?.length ?? 0) + 1,
      )
    : 0;
  const contentWidth = Math.max(1, safeWidth - frameInset - yWidth);
  const contentHeight = Math.max(1, safeHeight - frameInset - titleRows - legendRows - xRows);
  const body =
    typeof children === "function"
      ? children({ width: contentWidth, height: contentHeight })
      : children;
  const borderColor = capabilityColor(colors.border, caps);
  const textColor = capabilityColor(colors.text, caps);

  const content = (
    <>
      {borderless ? (
        <text wrapMode="none" truncate {...colorProp("fg", textColor)}>
          <strong>{fitChartText(title, Math.max(1, safeWidth))}</strong>
        </text>
      ) : null}
      {legend.length ? (
        <box height={1} flexDirection="row" overflow="hidden">
          <text wrapMode="none" truncate>
            {legend.map((item, index) => (
              <span
                key={`${item.label}-${index}`}
                {...colorProp("fg", capabilityColor(item.color ?? colors.text, caps))}
              >
                {item.marker ?? "■"} {item.label}
                {index < legend.length - 1 ? "  " : ""}
              </span>
            ))}
          </text>
        </box>
      ) : null}
      <box flexGrow={1} minHeight={1} flexDirection="row" overflow="hidden">
        {yAxis ? (
          <box
            width={yWidth}
            flexDirection="column"
            justifyContent="space-between"
            overflow="hidden"
          >
            <text wrapMode="none" {...colorProp("fg", textColor)}>
              {fitChartText(yAxis.maximum, yWidth)}
            </text>
            {yAxis.midpoint ? (
              <text wrapMode="none" {...colorProp("fg", textColor)}>
                {fitChartText(yAxis.midpoint, yWidth)}
              </text>
            ) : null}
            <text wrapMode="none" {...colorProp("fg", textColor)}>
              {fitChartText(yAxis.minimum, yWidth)}
            </text>
          </box>
        ) : null}
        <box flexGrow={1} minWidth={1} flexDirection="column" overflow="hidden">
          {body}
        </box>
      </box>
      {xAxis ? (
        <box
          height={1}
          marginLeft={yWidth}
          flexDirection="row"
          justifyContent="space-between"
          overflow="hidden"
        >
          <text wrapMode="none" {...colorProp("fg", textColor)}>
            {xAxis.minimum}
          </text>
          {xAxis.midpoint ? (
            <text wrapMode="none" {...colorProp("fg", textColor)}>
              {xAxis.midpoint}
            </text>
          ) : null}
          <text wrapMode="none" {...colorProp("fg", textColor)}>
            {xAxis.maximum}
          </text>
        </box>
      ) : null}
    </>
  );

  if (borderless)
    return (
      <box
        width={safeWidth}
        height={safeHeight}
        flexDirection="column"
        overflow="hidden"
        {...colorProp("backgroundColor", capabilityColor(colors.background, caps))}
      >
        {content}
      </box>
    );
  return (
    <box
      width={safeWidth}
      height={safeHeight}
      border={frameStyle === "open" ? ["top", "bottom"] : true}
      {...colorProp("borderColor", borderColor)}
      title={fitChartText(title, Math.max(1, safeWidth - 4)).trimEnd()}
      {...colorProp("titleColor", textColor)}
      {...colorProp("backgroundColor", capabilityColor(colors.background, caps))}
      flexDirection="column"
      overflow="hidden"
    >
      {content}
    </box>
  );
}

export default ChartFrame;
