# Kunpeng DevKit AI — Demo Wireframes（ASCII 交互稿）

> Version 0.2 · 四大 Demo · 可直接对齐 TUI 研发实现

---

## Demo 1 · AI Migration Agent（P0）

### Step 1 · 入口

```
╭─ DevKit AI ────────────────────────────────────╮
│                                                │
│   What do you want?                            │
│   ❯ migrate nginx project▌                     │
│                                                │
│   /migrate  /diagnose  /optimize  /observe     │
╰────────────────────────────────────────────────╯
```

### Step 2 · Plan 确认

```
╭─ Migration Agent ──────────────────────────────╮
│ Project  /home/user/nginx                      │
│ Source   x86_64          Target  Kunpeng ARM64 │
├────────────────────────────────────────────────┤
│ AI Plan                                        │
│  1. Analyze dependency                         │
│  2. Find incompatible API   (knowledge_search) │
│  3. Generate patches        (code_cpp_migrator)│
│  4. Build verify                               │
│  5. Benchmark                                  │
│                                                │
│ [E]xecute   [M]odify   [C]ancel                │
╰────────────────────────────────────────────────╯
```

### Step 3 · Agent 执行流

```
│ Agent Console                                  │
│ ● Source Scan                1,204 files  1.2s │
│ ● Dependency Analysis        18 libs           │
│ ▶ API Compatibility  ⠹       tool:cpp_migrator │
│ ○ Generate Patch                               │
│ ○ Build Verify                                 │
```

### Step 4 · 迁移报告

```
╭─ Migration Report · nginx ─────────────────────╮
│ Compatibility  ████████░░ 82%                  │
│ Critical 2 · Warning 8 · Auto-fixable 21       │
├────────────────────────────────────────────────┤
│ Issues                    Files                │
│ ├ SSE instruction  ⚠      src/                 │
│ │   crypto.c:88           ├ crypto.c  ███████  │
│ ├ atomic API       ⚠      ├ memory.c  ████     │
│ │   memory.c:223          └ build.mk  ██       │
│ └ Makefile flags   ✓                           │
│                                                │
│ [Enter] detail   [P] generate patches          │
╰────────────────────────────────────────────────╯
```

### Step 5 · Patch Review

```
╭─ Patch 2/12 · src/crypto.c ────────────────────╮
│ - _mm_pause();                                 │
│ + asm volatile("yield");                       │
│                                                │
│ Evidence: 指令替换案例库 #4471 · ARM ARM §B2.5   │
│ Impact:   Compatibility Fixed · Perf +3%       │
│                                                │
│ [A]ccept  [E]dit  [R]eject  [Space] next       │
╰────────────────────────────────────────────────╯
```

### Step 6 · 验证与总结

```
╭─ Session Summary · migrate nginx ──────────────╮
│ ✓ 21 fixed   ⚠ 2 manual review                 │
│ Build  PASS                                    │
│ Bench  100ms → 70ms  (−30%)                    │
│        ██████████     ███████                  │
│ [S]ave report  [N]ew task                      │
╰────────────────────────────────────────────────╯
```

---

## Demo 2 · AI Performance Optimize（P1）

### 入口

```
❯ optimize model.bin
```

### Dashboard

```
╭─ Performance Overview · Qwen-72B ──────────────╮
│ Latency 120ms   Throughput 80%   Mem 42GB      │
├────────────────────────────────────────────────┤
│ Timeline        0ms ─────────────── 120ms      │
│ CPU   ████████                                 │
│ NPU      █████████████                         │
│ Mem   ██████                                   │
├────────────────────────────────────────────────┤
│ Bottleneck Ranking                             │
│ attention  █████████  45%                      │
│ matmul     ███████    35%                      │
│ memcpy     ████       20%                      │
│                                                │
│ AI: attention is memory-bound  [Enter] why     │
╰────────────────────────────────────────────────╯
```

### 算子下钻 + AI 建议

```
╭─ Operator · MatMul 4096x4096 ──────────────────╮
│ Compute ███████ 70%    Memory ████ 30%         │
├────────────────────────────────────────────────┤
│ AI Proposal                                    │
│  ✓ Enable tiling                               │
│  ✓ Kernel fusion (Conv+Bias+Relu)              │
│  ✓ INT8 mixed precision                        │
│                                                │
│ Expected  20ms → 12ms  (−40%)                  │
│ [Y] Apply & Benchmark   [R] Review             │
╰────────────────────────────────────────────────╯
```

### Benchmark 对比

```
│ Before  ██████████  120ms                      │
│ After   ██████       70ms   (−42%)  ✓ verified │
```

---

## Demo 3 · AI Diagnose（P1）

### 入口

```
❯ diagnose crash.log
```

### 诊断结果

```
╭─ Crash Diagnosis ──────────────────────────────╮
│ Signal  SIGSEGV                                │
├────────────────────────────────────────────────┤
│ Problem Graph                                  │
│  app                                           │
│   │                                            │
│  runtime.so                                    │
│   │                                            │
│  memory allocator                              │
│   │                                            │
│  unaligned access   ◀ Root Cause               │
│  ═══════════════                               │
│                                                │
│ Confidence  █████████░ 91%                     │
│                                                │
│ Evidence                                       │
│  [1] runtime.log:223  "unaligned access"       │
│  [2] kernel.c:88                               │
│  [3] ARM ARM §B2.5                             │
├────────────────────────────────────────────────┤
│ Fix: replace malloc → aligned_alloc            │
│ [Y] Apply fix   [R] Review diff   [N] Dismiss  │
╰────────────────────────────────────────────────╯
```

---

## Demo 4 · Observe（P2）

### System Dashboard

```
╭─ System ───────────────────────────────────────╮
│ ┌ CPU ─────────┐ ┌ NPU ─────────┐ ┌ Mem ─────┐ │
│ │ ███████ 70%  │ │ █████████90% │ │ ████ 40% │ │
│ │ ▂▃▅▇▆▃▂      │ │ ▅▆▇█▇▆▅      │ │ ▃▃▄▄▄▃▃  │ │
│ │ 54°C         │ │ 72°C  ⚠      │ │ 26/64GB  │ │
│ └──────────────┘ └──────────────┘ └──────────┘ │
├────────────────────────────────────────────────┤
│ Top Task                                       │
│ llama_inference   NPU ████████ 82%             │
│ compile_worker    CPU ████     35%             │
├────────────────────────────────────────────────┤
│ ❯ top 10 slow kernel                           │
│ kernel1 ███████ 30ms  kernel2 █████ 20ms       │
╰────────────────────────────────────────────────╯
```

### Trace Viewer

```
╭─ Trace ────────────── [+/-] zoom [f] filter ───╮
│        0ms                          100ms      │
│ CPU    ████████                                │
│ GPU       ███████                              │
│ NPU          ██████████                        │
│              └ matmul   attention   softmax    │
│                          ▲ selected: 18ms      │
│                            mem-bound ⚠         │
╰────────────────────────────────────────────────╯
```
