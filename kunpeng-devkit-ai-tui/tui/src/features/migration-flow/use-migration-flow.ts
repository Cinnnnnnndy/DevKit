import { useEffect, useMemo, useSyncExternalStore } from "react";
import type { DevKitGateway, ReportExporter } from "../../data/ports";
import { MigrationFlowController } from "./controller";
import type { MigrationFlowState } from "./types";

export interface UseMigrationFlowOptions {
  readonly gateway: DevKitGateway;
  readonly reportExporter?: ReportExporter;
  readonly autoStart?: boolean;
}

export interface MigrationFlowBinding {
  readonly state: MigrationFlowState;
  readonly controller: MigrationFlowController;
}

export function useMigrationFlow({
  gateway,
  reportExporter,
  autoStart = true,
}: UseMigrationFlowOptions): MigrationFlowBinding {
  const controller = useMemo(
    () => new MigrationFlowController({ gateway, ...(reportExporter ? { reportExporter } : {}) }),
    [gateway, reportExporter],
  );
  const state = useSyncExternalStore(
    controller.subscribe,
    controller.getSnapshot,
    controller.getSnapshot,
  );

  useEffect(() => {
    if (autoStart) void controller.start();
    return () => controller.cancelCurrent();
  }, [autoStart, controller]);

  return { state, controller };
}
