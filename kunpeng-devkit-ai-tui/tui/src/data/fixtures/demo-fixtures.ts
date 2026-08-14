import type {
  BuildDiagnosis,
  BuildReport,
  ConfigurationRequirement,
  MigrationPlan,
  MigrationReport,
  PatchReviewBundle,
  PerformanceBaseline,
  ScenarioProfile,
  ScenarioProfileResult,
  SessionSummary,
  TuningComparison,
  WorkspaceBootstrap,
} from "../../domain";

export type MockScenario = "happy" | "empty" | "error" | "slow" | "offline" | "extreme";

export interface DemoFixtureSet {
  readonly workspace: WorkspaceBootstrap;
  readonly plan: MigrationPlan;
  readonly configuration: ConfigurationRequirement;
  readonly migrationReport: MigrationReport;
  readonly patchReview: PatchReviewBundle;
  readonly failedBuild: BuildReport;
  readonly passedBuild: BuildReport;
  readonly diagnosis: BuildDiagnosis;
  readonly performance: PerformanceBaseline;
  readonly tuning: TuningComparison;
  readonly profiles: readonly ScenarioProfile[];
  readonly profileResult: ScenarioProfileResult;
  readonly summary: SessionSummary;
}

const TASK_ID = "task-nginx-arm64";
const SESSION_ID = "session-demo-001";

const happyFixtures: DemoFixtureSet = {
  workspace: {
    productName: "Kunpeng DevKit AI",
    binaryName: "devkitai",
    version: "0.1.0",
    sessionId: SESSION_ID,
    runtimeReady: true,
    sourceArchitecture: "x86_64",
    targetArchitecture: "aarch64",
    capabilities: [
      {
        id: "knowledge-base",
        name: "kunpeng_knowledge_base_search",
        description: "鲲鹏知识库检索",
        status: "ready",
      },
      {
        id: "cpp-migrator",
        name: "code_cpp_migrator",
        description: "C/C++ 源码迁移",
        status: "ready",
      },
      {
        id: "sql-migrator",
        name: "database_sql_migrator",
        description: "SQL 智能迁移",
        status: "missing",
      },
      {
        id: "profiler",
        name: "profiler",
        description: "性能剖析",
        status: "blocked",
        reason: "需要 NPU driver ≥ 23.0",
      },
    ],
    recentTasks: [
      {
        id: TASK_ID,
        label: "migrate nginx",
        status: "paused",
        updatedAt: "2026-08-10T09:30:00.000Z",
        summary: "兼容性 82% · 2 项待人工确认",
      },
    ],
    suggestions: ["安装迁移能力包", "扫描当前工程", "继续上次任务"],
  },
  plan: {
    taskId: TASK_ID,
    goal: "将 ./nginx 从 x86_64 迁移到 Kunpeng ARM64 并完成性能验证",
    sourcePath: "./nginx",
    sourceArchitecture: "x86_64",
    targetArchitecture: "aarch64",
    version: 1,
    estimatedDurationMs: 180_000,
    steps: [
      {
        id: "analyze-dependencies",
        title: "分析工程与依赖",
        description: "识别构建系统、依赖和目标架构",
        status: "pending",
        tool: "code_cpp_migrator",
      },
      {
        id: "find-incompatibilities",
        title: "定位不兼容 API 与指令",
        description: "结合知识库生成证据",
        status: "pending",
        tool: "kunpeng_knowledge_base_search",
      },
      {
        id: "generate-patches",
        title: "生成迁移补丁",
        description: "逐文件生成可审查 Diff",
        status: "pending",
        tool: "code_cpp_migrator",
      },
      {
        id: "build-verify",
        title: "编译验证",
        description: "使用 aarch64 工具链验证构建",
        status: "pending",
      },
      {
        id: "benchmark",
        title: "性能基线",
        description: "采集 QPS、P99 与资源利用率",
        status: "pending",
        tool: "profiler",
      },
    ],
  },
  configuration: {
    taskId: TASK_ID,
    resumeToken: "resume-build-verify-001",
    pausedStepId: "build-verify",
    reason: "未探测到 aarch64 交叉编译工具链，需要补充配置后继续编译验证。",
    fields: [
      {
        key: "toolchainPath",
        label: "工具链路径",
        kind: "path",
        required: true,
        sensitive: false,
        defaultValue: "/usr/bin/aarch64-linux-gnu-",
        hint: "Tab 补全",
      },
      {
        key: "outputDirectory",
        label: "输出目录",
        kind: "path",
        required: true,
        sensitive: false,
        defaultValue: "./build-arm64",
      },
      {
        key: "parallelism",
        label: "并行度",
        kind: "integer",
        required: true,
        sensitive: false,
        defaultValue: 16,
        hint: "检测到 16 个逻辑核",
      },
    ],
    canSkip: true,
  },
  migrationReport: {
    taskId: TASK_ID,
    compatibilityScore: 82,
    criticalCount: 2,
    warningCount: 8,
    autoFixableCount: 21,
    files: [
      { path: "src/crypto.c", risk: 0.96, issueCount: 8 },
      { path: "src/event/ngx_event.c", risk: 0.67, issueCount: 5 },
      { path: "src/core/ngx_cycle.c", risk: 0.34, issueCount: 2 },
      { path: "auto/cc/gcc", risk: 0.18, issueCount: 1 },
    ],
    issues: [
      {
        id: "issue-mm-pause",
        severity: "critical",
        title: "x86 SSE 指令在 ARM64 上不可用",
        file: "src/crypto.c",
        line: 223,
        autoFixable: true,
        evidence: [
          {
            id: "evidence-mm-pause-source",
            kind: "source",
            label: "src/crypto.c:223",
            locator: "src/crypto.c#L223",
            excerpt: "_mm_pause();",
          },
          {
            id: "evidence-mm-pause-kb",
            kind: "knowledge",
            label: "指令替换案例 #4471",
            locator: "kb://arm-migration/4471",
          },
        ],
      },
      {
        id: "issue-alignment",
        severity: "critical",
        title: "内存分配未满足 ARM64 对齐要求",
        file: "src/os/unix/ngx_alloc.c",
        line: 87,
        autoFixable: false,
        evidence: [
          {
            id: "evidence-alignment-manual",
            kind: "manual",
            label: "ARM Architecture Reference Manual §B2.5",
            locator: "manual://arm-arm/B2.5",
          },
        ],
      },
    ],
    generatedAt: "2026-08-13T02:00:00.000Z",
  },
  patchReview: {
    taskId: TASK_ID,
    acceptedCount: 0,
    rejectedCount: 0,
    pendingCount: 2,
    patches: [
      {
        id: "patch-mm-pause",
        issueId: "issue-mm-pause",
        file: "src/crypto.c",
        summary: "使用 ARM yield 替换 x86 pause 指令",
        impact: "修复 ARM64 兼容性，保持自旋等待语义",
        decision: "pending",
        lines: [
          { kind: "context", oldLine: 222, newLine: 222, content: "while (locked) {" },
          { kind: "deletion", oldLine: 223, content: "  _mm_pause();" },
          { kind: "addition", newLine: 223, content: '  __asm__ volatile("yield");' },
          { kind: "context", oldLine: 224, newLine: 224, content: "}" },
        ],
        evidence: [
          {
            id: "patch-evidence-4471",
            kind: "knowledge",
            label: "迁移案例 #4471",
            locator: "kb://arm-migration/4471",
          },
        ],
      },
      {
        id: "patch-build-flags",
        issueId: "issue-build-flags",
        file: "auto/cc/gcc",
        summary: "移除 x86 专用编译参数",
        impact: "允许 aarch64 编译器完成配置探测",
        decision: "pending",
        lines: [
          { kind: "deletion", oldLine: 41, content: 'CFLAGS="$CFLAGS -msse4.2"' },
          { kind: "addition", newLine: 41, content: 'CFLAGS="$CFLAGS -march=armv8.2-a"' },
        ],
        evidence: [
          {
            id: "patch-evidence-armv8-flags",
            kind: "knowledge",
            label: "ARMv8.2-A 编译参数指南",
            locator: "kb://arm-migration/compiler-flags/armv8.2-a",
          },
        ],
      },
    ],
  },
  failedBuild: {
    taskId: TASK_ID,
    status: "failed",
    command: "make -j16 CC=aarch64-linux-gnu-gcc",
    durationMs: 14_800,
    output: [
      "[ 84%] Building C object src/os/unix/ngx_alloc.o",
      "error: requested alignment 8 is less than minimum 16",
      "make: *** [src/os/unix/ngx_alloc.o] Error 1",
    ],
    artifacts: [],
    failure: {
      code: "BUILD_ALIGNMENT_ERROR",
      message: "requested alignment 8 is less than minimum 16",
      file: "src/os/unix/ngx_alloc.c",
      line: 87,
    },
  },
  passedBuild: {
    taskId: TASK_ID,
    status: "passed",
    command: "make -j16 CC=aarch64-linux-gnu-gcc",
    durationMs: 12_420,
    output: ["[100%] Linking C executable objs/nginx", "Build PASS"],
    artifacts: ["build-arm64/objs/nginx"],
  },
  diagnosis: {
    taskId: TASK_ID,
    rootCause: "ARM64 内存对齐要求未满足",
    confidence: 0.91,
    nodes: [
      { id: "app", label: "nginx build", kind: "problem" },
      { id: "allocator", label: "ngx_alloc", kind: "evidence" },
      { id: "unaligned", label: "8-byte alignment", kind: "root-cause" },
      { id: "fix", label: "aligned_alloc(16, size)", kind: "solution" },
    ],
    edges: [
      { from: "app", to: "allocator" },
      { from: "allocator", to: "unaligned" },
      { from: "unaligned", to: "fix" },
    ],
    evidence: [
      {
        id: "diagnosis-build-log",
        kind: "log",
        label: "build.log:482",
        locator: "build.log#L482",
        excerpt: "requested alignment 8 is less than minimum 16",
      },
      {
        id: "diagnosis-source",
        kind: "source",
        label: "src/os/unix/ngx_alloc.c:87",
        locator: "src/os/unix/ngx_alloc.c#L87",
      },
    ],
    proposedFixId: "fix-aligned-alloc",
    proposedFixSummary: "将 malloc 替换为 16 字节 aligned_alloc",
    canApplyAutomatically: true,
  },
  performance: {
    taskId: TASK_ID,
    bottleneck: "memory-bound",
    metrics: { qps: 42_000, p99LatencyMs: 18, cpuPercent: 62, memoryGiB: 4.2 },
    hbmUtilizationPercent: 93,
    npuUtilizationPercent: 48,
    trace: [
      {
        id: "cpu",
        label: "CPU",
        spans: [
          { id: "cpu-accept", label: "accept", startMs: 0, durationMs: 24, intensity: 0.56 },
          { id: "cpu-worker", label: "worker", startMs: 28, durationMs: 62, intensity: 0.82 },
        ],
      },
      {
        id: "memory",
        label: "Memory",
        spans: [{ id: "mem-copy", label: "memcpy", startMs: 8, durationMs: 84, intensity: 0.96 }],
      },
    ],
    evidence: [
      {
        id: "metric-hbm",
        kind: "metric",
        label: "HBM bandwidth 93%",
        locator: "trace://baseline/hbm",
      },
    ],
  },
  tuning: {
    taskId: TASK_ID,
    baseline: { qps: 42_000, p99LatencyMs: 18, cpuPercent: 62, memoryGiB: 4.2 },
    plans: [
      {
        id: "plan-a",
        name: "方案 A",
        recommended: true,
        description: "物理核对齐与 NUMA 亲和绑定",
        metrics: { qps: 61_000, p99LatencyMs: 12, cpuPercent: 78, memoryGiB: 5.1 },
        changes: [
          {
            key: "worker_processes",
            before: "auto",
            after: "64",
            reason: "对齐 64 个物理核",
          },
          {
            key: "worker_connections",
            before: "1024",
            after: "8192",
            reason: "匹配实测并发水位",
          },
          { key: "numa", before: "off", after: "per-worker", reason: "消除跨 NUMA 访问" },
        ],
        tradeoffs: ["内存增加 0.9 GiB"],
      },
      {
        id: "plan-b",
        name: "方案 B",
        recommended: false,
        description: "激进低延迟配置",
        metrics: { qps: 55_000, p99LatencyMs: 9, cpuPercent: 88, memoryGiB: 6.8 },
        changes: [{ key: "busy_poll", before: "off", after: "on", reason: "减少事件等待时间" }],
        tradeoffs: ["CPU 占用升至 88%", "内存增加至 6.8 GiB"],
      },
    ],
  },
  profiles: [
    {
      id: "high-concurrency-short-connection",
      name: "高并发短连接",
      description: "优化连接建立、事件循环和端口复用",
      recommendedFor: ["API Gateway", "短请求服务"],
      estimatedDurationMs: 90_000,
    },
    {
      id: "large-static-file",
      name: "大文件传输",
      description: "优化 sendfile、缓存和网络缓冲区",
      recommendedFor: ["静态资源服务"],
      estimatedDurationMs: 120_000,
    },
  ],
  profileResult: {
    taskId: TASK_ID,
    profileId: "high-concurrency-short-connection",
    status: "passed",
    metrics: { qps: 64_200, p99LatencyMs: 10.8, cpuPercent: 81, memoryGiB: 5.3 },
    observations: ["连接建立耗时下降 18%", "TIME_WAIT 峰值下降 31%"],
  },
  summary: {
    sessionId: SESSION_ID,
    taskId: TASK_ID,
    title: "nginx x86_64 → Kunpeng ARM64",
    fixedIssueCount: 21,
    manualReviewCount: 2,
    buildStatus: "passed",
    baseline: { qps: 42_000, p99LatencyMs: 18, cpuPercent: 62, memoryGiB: 4.2 },
    finalMetrics: { qps: 61_000, p99LatencyMs: 12, cpuPercent: 78, memoryGiB: 5.1 },
    modifiedFiles: ["src/crypto.c", "src/os/unix/ngx_alloc.c", "auto/cc/gcc"],
    pendingActions: ["人工审查 2 个非自动修复项"],
    generatedAt: "2026-08-13T03:00:00.000Z",
  },
};

function emptyFixtures(): DemoFixtureSet {
  const fixtures = structuredClone(happyFixtures);
  return {
    ...fixtures,
    workspace: { ...fixtures.workspace, capabilities: [], recentTasks: [], suggestions: [] },
    plan: { ...fixtures.plan, steps: [] },
    migrationReport: {
      ...fixtures.migrationReport,
      compatibilityScore: 100,
      criticalCount: 0,
      warningCount: 0,
      autoFixableCount: 0,
      files: [],
      issues: [],
    },
    patchReview: {
      ...fixtures.patchReview,
      patches: [],
      acceptedCount: 0,
      rejectedCount: 0,
      pendingCount: 0,
    },
    performance: { ...fixtures.performance, trace: [], evidence: [] },
    tuning: { ...fixtures.tuning, plans: [] },
    profiles: [],
    summary: { ...fixtures.summary, modifiedFiles: [], pendingActions: [] },
  };
}

function extremeFixtures(): DemoFixtureSet {
  const fixtures = structuredClone(happyFixtures);
  const manyFiles = Array.from({ length: 256 }, (_, index) => ({
    path: `src/非常长的模块名称-${String(index).padStart(3, "0")}/architecture_specific_implementation.c`,
    risk: (index % 101) / 100,
    issueCount: (index * 17) % 97,
  }));
  return {
    ...fixtures,
    migrationReport: {
      ...fixtures.migrationReport,
      compatibilityScore: 1,
      criticalCount: 9_999,
      warningCount: 99_999,
      autoFixableCount: 1_000_000,
      files: manyFiles,
    },
    performance: {
      ...fixtures.performance,
      metrics: {
        qps: Number.MAX_SAFE_INTEGER,
        p99LatencyMs: 0.001,
        cpuPercent: 100,
        memoryGiB: 1_048_576,
      },
    },
  };
}

export function createDemoFixtures(scenario: MockScenario): DemoFixtureSet {
  switch (scenario) {
    case "empty":
      return emptyFixtures();
    case "extreme":
      return extremeFixtures();
    case "happy":
    case "error":
    case "slow":
    case "offline":
      return structuredClone(happyFixtures);
  }
}
