import { colorProp } from "./color-props.js";
import { useUiEnvironment } from "./theme-context.js";

/**
 * 标识按可用宽度分三档，低于最小宽度**不画**，不缩着画。
 *
 * 不保留「只有标记」这一档是有意的：终端里标记没有尺寸和位置线索，
 * 一个孤立的红色字形读不出身份，而 `VIS-SEM-01` 又把 Kunpeng 红
 * 专门留给身份——它会和 danger 的语义撞车，比不画更糟。
 */
export type BrandVariant = "full" | "wordmark" | "none";

/** `◢` + ` KUNPENG ` + ` DEVKIT AI ` = 21 列；多留 1 列容纳 `◢` 的歧义宽度。 */
export const BRAND_FULL_MIN_WIDTH = 22;
/** `◢` + ` KUNPENG` = 9 列；同样多留 1 列。 */
export const BRAND_WORDMARK_MIN_WIDTH = 10;

export function brandVariantFor(available: number): BrandVariant {
  if (!Number.isFinite(available)) return "none";
  if (available >= BRAND_FULL_MIN_WIDTH) return "full";
  if (available >= BRAND_WORDMARK_MIN_WIDTH) return "wordmark";
  return "none";
}

export function KunpengBrand({ available }: { available: number }) {
  const { theme, capabilities } = useUiEnvironment();
  const variant = brandVariantFor(available);
  if (variant === "none") return null;

  const mark = capabilities.unicode ? "◢" : ">";
  return (
    <box height={1} flexDirection="row" flexShrink={0}>
      <text {...colorProp("fg", theme.kunpeng)}>
        <strong>{mark}</strong>
      </text>
      <text {...colorProp("fg", theme.foreground)}>
        {" "}
        <strong>KUNPENG</strong>
        {variant === "full" ? " " : ""}
      </text>
      {variant === "full" ? (
        <text {...colorProp("fg", theme.foreground)} {...colorProp("bg", theme.surface4)}>
          <strong> DEVKIT AI </strong>
        </text>
      ) : null}
    </box>
  );
}
