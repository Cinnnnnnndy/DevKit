import type { ExportedReport, ExportSessionReportRequest } from "../../../domain";
import { cancelledError, createAppError, err, ok, type Result } from "../../../shared";
import type { ReportExporter } from "../../ports";

export class MemoryReportExporter implements ReportExporter {
  private readonly reports = new Map<string, string>();

  async exportReport(
    request: ExportSessionReportRequest,
    signal: AbortSignal,
  ): Promise<Result<ExportedReport>> {
    // Yield before the in-memory write so callers can cancel immediately after starting the export.
    await Promise.resolve();
    if (signal.aborted) return err(cancelledError());
    try {
      const content =
        request.format === "json"
          ? JSON.stringify(request.summary, null, 2)
          : this.toMarkdown(request.summary);
      this.reports.set(request.destinationPath, content);
      return ok({
        destinationPath: request.destinationPath,
        byteLength: new TextEncoder().encode(content).byteLength,
        format: request.format,
      });
    } catch (cause) {
      return err(
        createAppError("unexpected", "report.export.failed", "报告导出失败", false, {
          cause: cause instanceof Error ? cause.message : String(cause),
        }),
      );
    }
  }

  read(destinationPath: string): string | undefined {
    return this.reports.get(destinationPath);
  }

  private toMarkdown(summary: ExportSessionReportRequest["summary"]): string {
    const qpsGain = summary.finalMetrics.qps - summary.baseline.qps;
    return [
      `# ${summary.title}`,
      "",
      `- Build: ${summary.buildStatus.toUpperCase()}`,
      `- 已修复：${summary.fixedIssueCount}`,
      `- 待人工审查：${summary.manualReviewCount}`,
      `- QPS：${summary.baseline.qps} → ${summary.finalMetrics.qps} (${qpsGain >= 0 ? "+" : ""}${qpsGain})`,
      `- 生成时间：${summary.generatedAt}`,
      "",
      "## 修改文件",
      ...summary.modifiedFiles.map((file) => `- ${file}`),
      "",
      "## 待办",
      ...summary.pendingActions.map((action) => `- ${action}`),
      "",
    ].join("\n");
  }
}
