import { CliRenderEvents, createCliRenderer } from "@opentui/core";
import { createRoot } from "@opentui/react";
import { App, type AppScreen, BUILD_VERSION } from "./app/index.js";
import {
  createMockDevKitGatewayFromEnvironment,
  MemoryReportExporter,
} from "./data/adapters/mock/index.js";
import { detectTerminalCapabilities } from "./platform/terminal/index.js";

async function runSmokeRender(): Promise<void> {
  const renderer = await createCliRenderer({
    bufferedOutput: "memory",
    clearOnShutdown: false,
    consoleMode: "disabled",
    exitOnCtrlC: false,
    exitSignals: [],
    screenMode: "main-screen",
    useKittyKeyboard: null,
    useMouse: false,
  });
  const root = createRoot(renderer);
  try {
    const firstFrame = new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => {
        cleanup();
        reject(new Error("OpenTUI smoke render timed out before its first frame"));
      }, 3_000);
      const cleanup = () => {
        clearTimeout(timeout);
        renderer.off(CliRenderEvents.FRAME, onFrame);
        renderer.off(CliRenderEvents.RENDER_ERROR, onRenderError);
      };
      const onFrame = () => {
        cleanup();
        resolve();
      };
      const onRenderError = ({ error }: { error: Error }) => {
        cleanup();
        reject(error);
      };
      renderer.once(CliRenderEvents.FRAME, onFrame);
      renderer.once(CliRenderEvents.RENDER_ERROR, onRenderError);
    });

    root.render(
      <box width={8} height={1}>
        <text>SMOKE</text>
      </box>,
    );
    renderer.requestRender();
    await firstFrame;
    await renderer.idle();
    root.unmount();
  } finally {
    renderer.destroy();
  }
  process.stdout.write("devkitai smoke-render ok\n");
}

if (process.argv.includes("--version") || process.argv.includes("-v")) {
  process.stdout.write(`devkitai ${BUILD_VERSION}\n`);
  process.exit(0);
}

if (process.argv.includes("--help") || process.argv.includes("-h")) {
  process.stdout.write(
    "Kunpeng DevKit AI native terminal workspace\n\n" +
      "Usage: devkitai [options]\n\n" +
      "Options:\n" +
      "  -h, --help       Show help\n" +
      "  -v, --version    Show version\n\n" +
      "Environment:\n" +
      "  DEVKITAI_MOCK_SCENARIO  happy|empty|error|slow|offline|extreme\n" +
      "  NO_COLOR                Disable terminal colors\n",
  );
  process.exit(0);
}

if (process.argv.includes("--smoke-render")) {
  await runSmokeRender();
  process.exit(0);
}

const screenArgument = process.argv.find((argument) => argument.startsWith("--screen="));
const requestedScreen = screenArgument?.slice("--screen=".length);
const initialScreen: AppScreen =
  requestedScreen === "charts" ||
  requestedScreen === "components" ||
  requestedScreen === "patterns" ||
  requestedScreen === "workbench"
    ? requestedScreen
    : "landing";
const patternArgument = process.argv.find((argument) => argument.startsWith("--pattern="));
const requestedPattern = Number.parseInt(patternArgument?.slice("--pattern=".length) ?? "1", 10);
const initialPattern = Math.max(
  0,
  Math.min(25, Number.isFinite(requestedPattern) ? requestedPattern - 1 : 0),
);

const capabilities = detectTerminalCapabilities();
const gateway = createMockDevKitGatewayFromEnvironment();
const reportExporter = new MemoryReportExporter();
const renderer = await createCliRenderer({ exitOnCtrlC: false, useMouse: capabilities.mouse });
renderer.setTerminalTitle("Kunpeng DevKit AI");

let exiting = false;
const exitApplication = () => {
  if (exiting) return;
  exiting = true;
  renderer.destroy();
  process.exit(0);
};

process.once("SIGTERM", exitApplication);
createRoot(renderer).render(
  <App
    gateway={gateway}
    reportExporter={reportExporter}
    capabilities={capabilities}
    initialScreen={initialScreen}
    initialPattern={initialPattern}
    onExit={exitApplication}
  />,
);
