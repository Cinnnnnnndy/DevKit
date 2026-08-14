import { createContext, type ReactNode, useContext, useMemo } from "react";
import {
  DEFAULT_TERMINAL_CAPABILITIES,
  type TerminalCapabilities,
} from "../../platform/terminal/index.js";
import { type ThemeTokens, tokensFor } from "../../theme/index.js";

export interface UiEnvironment {
  capabilities: TerminalCapabilities;
  theme: ThemeTokens;
}

const DEFAULT_ENVIRONMENT: UiEnvironment = {
  capabilities: DEFAULT_TERMINAL_CAPABILITIES,
  theme: tokensFor(DEFAULT_TERMINAL_CAPABILITIES),
};

const UiEnvironmentContext = createContext<UiEnvironment>(DEFAULT_ENVIRONMENT);

export function UiProvider({
  capabilities = DEFAULT_TERMINAL_CAPABILITIES,
  children,
}: {
  capabilities?: TerminalCapabilities;
  children: ReactNode;
}) {
  const value = useMemo<UiEnvironment>(
    () => ({ capabilities, theme: tokensFor(capabilities) }),
    [capabilities],
  );
  return <UiEnvironmentContext.Provider value={value}>{children}</UiEnvironmentContext.Provider>;
}

export function useUiEnvironment(): UiEnvironment {
  return useContext(UiEnvironmentContext);
}
