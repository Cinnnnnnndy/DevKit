import type { ExportedReport, ExportSessionReportRequest } from "../../domain";
import type { Result } from "../../shared";

export interface ReportExporter {
  exportReport(
    request: ExportSessionReportRequest,
    signal: AbortSignal,
  ): Promise<Result<ExportedReport>>;
}
