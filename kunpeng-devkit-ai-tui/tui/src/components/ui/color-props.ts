import type { ThemeColor } from "../../theme/index.js";

export type UiColorPropName =
  | "backgroundColor"
  | "bg"
  | "borderColor"
  | "cursorColor"
  | "defaultColor"
  | "fg"
  | "focusedBackgroundColor"
  | "focusedTextColor"
  | "placeholderColor"
  | "textColor"
  | "titleColor";

/**
 * Builds an exact-optional OpenTUI color prop.
 *
 * `NO_COLOR` themes resolve every color token to `undefined`; returning an
 * empty object in that case prevents React/OpenTUI from receiving an explicit
 * foreground, background or border color while keeping strict optional types.
 */
export function colorProp<Name extends UiColorPropName>(
  name: Name,
  color: ThemeColor,
): { [Key in Name]?: string } {
  return color === undefined ? {} : ({ [name]: color } as { [Key in Name]?: string });
}
