import { describe, expect, it } from "vitest";
import { DEFAULT_TERMINAL_CAPABILITIES } from "../../../src/platform/terminal/index.js";
import { TRUE_COLOR_TOKENS, tokensFor } from "../../../src/theme/index.js";

describe("theme tokens", () => {
  it("exposes the PTO data ramps and Kunpeng identity colors", () => {
    expect(TRUE_COLOR_TOKENS.kunpengSecondary).toBe("#C9C9C9");
    expect(TRUE_COLOR_TOKENS.copyBlue).toEqual([
      "#052C75",
      "#094CCD",
      "#3C7CF6",
      "#76A3F9",
      "#B1CAFC",
    ]);
    expect(TRUE_COLOR_TOKENS.accumOrange).toHaveLength(7);
    expect(TRUE_COLOR_TOKENS.ubGreen[2]).toBe("#B3F141");
    expect(TRUE_COLOR_TOKENS.mteAmber[2]).toBe("#F4CB22");
    expect(TRUE_COLOR_TOKENS.violet[2]).toBe("#9B3CF6");
  });

  it("maps ANSI16 and NO_COLOR without losing token shape", () => {
    const ansi = tokensFor({ ...DEFAULT_TERMINAL_CAPABILITIES, colorMode: "ansi16" });
    const none = tokensFor({ ...DEFAULT_TERMINAL_CAPABILITIES, colorMode: "none" });
    expect(ansi.copyBlue).toHaveLength(TRUE_COLOR_TOKENS.copyBlue.length);
    expect(ansi.kunpeng).toBe("red");
    expect(none.kunpeng).toBeUndefined();
    expect(none.accumOrange.every((color) => color === undefined)).toBe(true);
  });
});
