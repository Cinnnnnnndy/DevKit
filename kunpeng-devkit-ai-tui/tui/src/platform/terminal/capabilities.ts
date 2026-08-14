export type TerminalColorMode = "truecolor" | "ansi16" | "none";

export interface TerminalCapabilities {
  colorMode: TerminalColorMode;
  unicode: boolean;
  braille: boolean;
  mouse: boolean;
  ssh: boolean;
  animations: "full" | "reduced" | "none";
}

export interface TerminalEnvironment {
  readonly [key: string]: string | undefined;
}

function isPresent(value: string | undefined): boolean {
  return value !== undefined && value !== "" && value !== "0";
}

export function detectTerminalCapabilities(
  environment: TerminalEnvironment = process.env,
): TerminalCapabilities {
  const term = environment["TERM"]?.toLowerCase() ?? "";
  const colorTerm = environment["COLORTERM"]?.toLowerCase() ?? "";
  const noColor = isPresent(environment["NO_COLOR"]) || term === "dumb";
  const truecolor =
    /truecolor|24bit/.test(colorTerm) ||
    /direct/.test(term) ||
    isPresent(environment["WT_SESSION"]);
  const ssh =
    isPresent(environment["SSH_CONNECTION"]) ||
    isPresent(environment["SSH_TTY"]) ||
    isPresent(environment["SSH_CLIENT"]);
  const unicode = environment["DEVKITAI_ASCII"] !== "1" && term !== "dumb";
  const braille = unicode && environment["DEVKITAI_NO_BRAILLE"] !== "1";
  const reducedMotion = ssh || environment["DEVKITAI_REDUCED_MOTION"] === "1";

  return {
    colorMode: noColor ? "none" : truecolor ? "truecolor" : "ansi16",
    unicode,
    braille,
    mouse: term !== "dumb" && environment["DEVKITAI_NO_MOUSE"] !== "1",
    ssh,
    animations: term === "dumb" ? "none" : reducedMotion ? "reduced" : "full",
  };
}

export const DEFAULT_TERMINAL_CAPABILITIES: TerminalCapabilities = {
  colorMode: "truecolor",
  unicode: true,
  braille: true,
  mouse: true,
  ssh: false,
  animations: "full",
};
