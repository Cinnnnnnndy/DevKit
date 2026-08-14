import { describe, expect, it } from "vitest";
import { detectTerminalCapabilities } from "../../../src/platform/terminal/capabilities.js";

describe("terminal capability detection", () => {
  it("recognizes Windows Terminal as TrueColor without COLORTERM", () => {
    expect(detectTerminalCapabilities({ WT_SESSION: "session-id" }).colorMode).toBe("truecolor");
  });

  it("keeps NO_COLOR authoritative in Windows Terminal", () => {
    expect(detectTerminalCapabilities({ WT_SESSION: "session-id", NO_COLOR: "1" }).colorMode).toBe(
      "none",
    );
  });
});
