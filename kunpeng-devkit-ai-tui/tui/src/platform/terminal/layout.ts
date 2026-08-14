export type ShellLayout =
  | "wide-three"
  | "wide-two-inspector"
  | "two-canvas"
  | "collapsed-dock"
  | "single-canvas"
  | "narrow";

export interface ShellLayoutMetrics {
  mode: ShellLayout;
  dockWidth: number;
  showDockContent: boolean;
  showSecondaryCanvas: boolean;
  showInspector: boolean;
  inspectorStrip: boolean;
  consoleHeight: number;
}

export function layoutForWidth(width: number): ShellLayoutMetrics {
  const safeWidth = Math.max(1, Math.floor(width));
  if (safeWidth >= 160)
    return {
      mode: "wide-three",
      dockWidth: 27,
      showDockContent: true,
      showSecondaryCanvas: true,
      showInspector: true,
      inspectorStrip: false,
      consoleHeight: 8,
    };
  if (safeWidth >= 140)
    return {
      mode: "wide-two-inspector",
      dockWidth: 25,
      showDockContent: true,
      showSecondaryCanvas: true,
      showInspector: true,
      inspectorStrip: true,
      consoleHeight: 8,
    };
  if (safeWidth >= 120)
    return {
      mode: "two-canvas",
      dockWidth: 23,
      showDockContent: true,
      showSecondaryCanvas: true,
      showInspector: false,
      inspectorStrip: false,
      consoleHeight: 7,
    };
  if (safeWidth >= 100)
    return {
      mode: "collapsed-dock",
      dockWidth: 3,
      showDockContent: false,
      showSecondaryCanvas: true,
      showInspector: false,
      inspectorStrip: false,
      consoleHeight: 7,
    };
  if (safeWidth >= 80)
    return {
      mode: "single-canvas",
      dockWidth: 3,
      showDockContent: false,
      showSecondaryCanvas: false,
      showInspector: false,
      inspectorStrip: false,
      consoleHeight: 6,
    };
  return {
    mode: "narrow",
    dockWidth: 0,
    showDockContent: false,
    showSecondaryCanvas: false,
    showInspector: false,
    inspectorStrip: false,
    consoleHeight: 5,
  };
}
