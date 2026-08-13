// Package dashboard implements the /chart Chart Workspace screen (a port of
// Scheme A's ChartWorkspace into the Scheme B visual language).
//
// The workspace is a second screen reachable by typing "/chart" in the Launch
// prompt. It shows one profiling capture shared by every pane — every chart
// reads the same cursor_index sample, so hover/click/arrow all move one cursor.
package dashboard

import (
	"fmt"
	"math"
)

// SampleCount is the number of simulated sampling points in the demo capture.
const SampleCount = 120

// Event is a point-in-time incident annotation on the timeline.
type Event struct {
	Sample   int
	Label    string
	Severity string // info | warning | danger
}

// Operator is one measured kernel: cost, memory, bound type and an 8-point
// share trend (used by the Hot-kernel race and, later, the Operators tab).
type Operator struct {
	Name      string
	Calls     int
	AverageMS float64
	TotalS    float64
	MemoryGB  float64
	Bound     string
	Trend     []int
}

// FlameNode is a single flame-graph frame (ported for the Flame tab).
type FlameNode struct {
	Name    string
	Start   int
	Percent int
	Depth   int
	SelfMS  float64
}

// TraceSegment is one activity span inside a trace lane.
type TraceSegment struct {
	Start     int
	Duration  int
	Intensity int
}

// TraceLane is one instance-level lane (Host / CPU-NUMA / NPU / Memory).
type TraceLane struct {
	Group      string
	Name       string
	Color      string
	Segments   []TraceSegment
	MaxIntensity int
}

// Worker is one runnable worker instance.
type Worker struct {
	Name       string
	CPU        int
	NUMA       int
	Migrations int
	RunQMS     float64
}

// Session is one coherent profiling capture shared by every chart pane.
type Session struct {
	Timestamps []string
	Latency    []float64
	Throughput []float64
	CPU        []float64
	CPUUser    []float64
	CPUSystem  []float64
	CPUIOwait  []float64
	RemoteNUMA []float64
	CoreUtil   [][]int // 120 x 64
	NodeUtil   [][]int // 120 x 4
	Events     []Event
	Operators  []Operator
	FlameNodes []FlameNode
	TraceLanes []TraceLane
	Workers    []Worker
}

// DefaultSession is the canonical demo capture used by the workspace.
// NewSession is a pure, deterministic function (only math.Sin — no rand), so
// tests can regenerate a deep-equal copy at any time.
var DefaultSession = NewSession()

// NewSession builds the demo capture. The formulas mirror Scheme A's
// MockProfilerSession.demo() exactly so the visible story is identical: after
// sample 72 a worker migration drives remote-NUMA from ~5% to ~21% and P99
// latency climbs to ~184ms (+37%), cores 34–38 go hot, and attention_fwd
// overtakes matmul_4096 in the hot-kernel race.
func NewSession() *Session {
	anchors := struct{ cpu, remote, latency, throughput []int }{
		cpu:        []int{48, 51, 49, 54, 57, 55, 59, 61, 58, 63, 65, 62, 66, 69, 73, 78, 82, 86, 84, 79, 76, 74, 72, 73},
		remote:     []int{4, 5, 4, 5, 6, 5, 5, 6, 5, 6, 7, 8, 9, 12, 16, 21, 23, 24, 22, 21, 20, 21, 21, 21},
		latency:    []int{126, 128, 124, 130, 132, 129, 134, 136, 131, 138, 141, 139, 146, 154, 166, 181, 193, 201, 197, 190, 187, 185, 184, 184},
		throughput: []int{57, 58, 59, 57, 56, 58, 57, 55, 56, 54, 53, 54, 52, 50, 48, 45, 42, 40, 40, 41, 42, 42, 43, 43},
	}

	timestamps := make([]string, SampleCount)
	for i := range timestamps {
		timestamps[i] = fmt.Sprintf("14:%02d:%02d", 32+i*3/60, i*3%60)
	}
	cpu := expand(anchors.cpu, 0.8)
	remote := expand(anchors.remote, 0.25)
	latency := expand(anchors.latency, 1.4)
	throughput := expand(anchors.throughput, 0.35)

	coreRows := make([][]int, SampleCount)
	nodeRows := make([][]int, SampleCount)
	for s := 0; s < SampleCount; s++ {
		core := make([]int, 64)
		for c := 0; c < 64; c++ {
			v := int(cpu[s]) + (c*17+s*7)%29 - 14
			if c >= 34 && c <= 38 && s >= 72 {
				v += 18 // worker migration → hot cores 34–38
			}
			core[c] = clamp(v, 18, 98)
		}
		coreRows[s] = core

		node := make([]int, 4)
		offsets := []int{-6, -13, 2, -18}
		if s >= 68 {
			offsets[2] = 12
		}
		for n, off := range offsets {
			node[n] = clamp(int(cpu[s])+off, 20, 98)
		}
		nodeRows[s] = node
	}

	iowait := make([]float64, SampleCount)
	for i, v := range cpu {
		iowait[i] = math.Max(2, v*0.09+(remote[i]-5)*0.42)
	}

	return &Session{
		Timestamps: timestamps,
		Latency:    latency,
		Throughput: throughput,
		CPU:        cpu,
		CPUUser:    mul(cpu, 0.73),
		CPUSystem:  mul(cpu, 0.18),
		CPUIOwait:  iowait,
		RemoteNUMA: remote,
		CoreUtil:   coreRows,
		NodeUtil:   nodeRows,
		Events: []Event{
			{57, "candidate-42 deployed", "info"},
			{72, "worker-27 migrated N0 → N2", "warning"},
			{78, "remote memory crossed 20%", "danger"},
			{88, "P99 regression alert +37%", "danger"},
		},
		Operators: []Operator{
			{"attention_fwd", 1024, 18.2, 18.6, 2.1, "memory", []int{5, 6, 6, 7, 9, 12, 17, 18}},
			{"matmul_4096", 512, 12.4, 6.3, 1.4, "compute", []int{6, 6, 7, 7, 7, 8, 8, 8}},
			{"layernorm", 2048, 0.8, 1.6, 0.12, "memory", []int{3, 3, 3, 4, 4, 4, 5, 5}},
			{"softmax", 1024, 1.2, 1.2, 0.25, "compute", []int{2, 2, 3, 3, 4, 4, 4, 4}},
			{"kv_cache_update", 1024, 0.6, 0.6, 3.8, "memory", []int{2, 3, 3, 5, 7, 9, 11, 12}},
			{"load_qkv", 1024, 4.8, 4.9, 2.8, "memory", []int{4, 4, 5, 6, 8, 11, 14, 16}},
			{"rope_apply", 1024, 1.1, 1.1, 0.18, "compute", []int{2, 2, 2, 3, 3, 4, 4, 5}},
			{"flash_decode", 512, 6.7, 3.4, 1.1, "mixed", []int{4, 5, 5, 6, 6, 7, 8, 8}},
			{"rms_norm", 2048, 0.7, 1.4, 0.09, "memory", []int{3, 3, 4, 4, 5, 5, 5, 6}},
			{"gelu_fused", 1024, 1.3, 1.3, 0.21, "compute", []int{2, 3, 3, 3, 4, 4, 5, 5}},
			{"all_reduce", 256, 4.1, 1.0, 0.8, "network", []int{2, 2, 3, 4, 4, 5, 6, 7}},
			{"embedding", 128, 5.9, 0.8, 3.2, "memory", []int{5, 5, 5, 6, 6, 7, 7, 7}},
			{"topk", 512, 1.4, 0.7, 0.12, "compute", []int{2, 2, 3, 3, 3, 4, 4, 5}},
			{"sampling", 512, 1.1, 0.6, 0.06, "compute", []int{1, 2, 2, 2, 3, 3, 4, 4}},
			{"memcpy_async", 4096, 0.1, 0.5, 4.6, "memory", []int{3, 4, 4, 6, 7, 9, 10, 12}},
			{"logits_proj", 512, 0.9, 0.5, 0.7, "compute", []int{2, 2, 2, 3, 3, 3, 4, 4}},
		},
		FlameNodes: []FlameNode{
			{"runtime.main", 0, 100, 0, 0.2},
			{"serve_loop", 1, 94, 1, 0.6}, {"telemetry", 96, 3, 1, 0.3},
			{"batch_dispatch", 2, 84, 2, 1.4}, {"idle_wait", 89, 6, 2, 0.2},
			{"inference.run", 4, 74, 3, 2.1}, {"tokenize", 80, 5, 3, 0.9},
			{"response_flush", 89, 4, 3, 0.4},
			{"embedding", 5, 9, 4, 4.9}, {"model.forward", 17, 58, 4, 3.2},
			{"sampling", 80, 4, 4, 0.8},
			{"decoder.layers", 18, 53, 5, 5.7}, {"logits_proj", 72, 3, 5, 1.1},
			{"attention", 19, 28, 6, 8.4}, {"mlp", 51, 14, 6, 6.1},
			{"rms_norm", 67, 4, 6, 1.7},
			{"attention_fwd", 20, 21, 7, 18.2}, {"softmax", 43, 4, 7, 2.2},
			{"gelu_fused", 52, 7, 7, 2.7}, {"matmul_4096", 61, 4, 7, 7.1},
			{"load_qkv", 21, 14, 8, 14.6}, {"rope_apply", 37, 4, 8, 3.1},
			{"remote_page_read", 22, 10, 9, 12.8}, {"memcpy_async", 33, 2, 9, 4.2},
			{"page_fault", 23, 5, 10, 7.9}, {"numa_migrate", 29, 3, 10, 5.4},
		},
		TraceLanes: makeTraceLanes(),
		Workers:    makeWorkers(),
	}
}

// expand interpolates len(values) anchors across SampleCount points with an
// optional sinusoidal wobble (mirrors Scheme A's expand()).
func expand(values []int, wobble float64) []float64 {
	out := make([]float64, SampleCount)
	for i := range out {
		position := float64(i) / float64(SampleCount-1) * float64(len(values)-1)
		left := minInt(len(values)-2, int(position))
		fraction := position - float64(left)
		out[i] = float64(values[left])*(1-fraction) + float64(values[left+1])*fraction
		out[i] += math.Sin(float64(i)*0.71) * wobble
	}
	return out
}

func mul(v []float64, k float64) []float64 {
	out := make([]float64, len(v))
	for i, x := range v {
		out[i] = x * k
	}
	return out
}

func clamp(v, lo, hi int) int {
	if v < lo {
		return lo
	}
	if v > hi {
		return hi
	}
	return v
}

func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// makeTraceLanes builds the deterministic 36-lane request trace.
func makeTraceLanes() []TraceLane {
	var lanes []TraceLane
	hostWorkers := []string{"main", "scheduler"}
	for i := 0; i < 12; i++ {
		hostWorkers = append(hostWorkers, fmt.Sprintf("worker-%02d", i))
	}
	hostWorkers = append(hostWorkers, "worker-18", "worker-27")

	definitions := []struct {
		group string
		names []string
		color string
	}{
		{"HOST", hostWorkers, "#3c7cf6"},
		{"CPU/NUMA", []string{"CPU 04", "CPU 11", "CPU 18", "CPU 25", "CPU 34", "CPU 36", "CPU 38", "CPU 45", "NUMA migrate"}, "#04d793"},
		{"NPU", []string{"stream-0", "stream-1", "stream-2", "stream-3", "cube", "vector"}, "#9b7bff"},
		{"MEMORY", []string{"HBM read", "HBM write", "DDR local", "DDR remote", "MTE DMA"}, "#ffaa3b"},
	}
	for _, def := range definitions {
		for _, name := range def.names {
			seed := len(lanes)*11 + 7
			segments := make([]TraceSegment, 0, 4)
			count := 3
			if def.group == "MEMORY" {
				count = 4
			}
			for seg := 0; seg < count; seg++ {
				segments = append(segments, TraceSegment{
					Start:     (seed + seg*23) % 88,
					Duration:  4 + (seed+seg*7)%12,
					Intensity: minInt(99, 28+(seed*3+seg*19)%72),
				})
			}
			if name == "worker-27" || name == "CPU 36" || name == "DDR remote" || name == "HBM read" {
				segments = append(segments, TraceSegment{44, 31, 98})
			}
			maxIntensity := 0
			for _, s := range segments {
				if s.Intensity > maxIntensity {
					maxIntensity = s.Intensity
				}
			}
			lanes = append(lanes, TraceLane{Group: def.group, Name: name, Color: def.color, Segments: segments, MaxIntensity: maxIntensity})
		}
	}
	return lanes
}

// makeWorkers builds the 32 runnable worker instances (worker-27 is the NUMA
// anomaly: high CPU, low NUMA affinity, frequent migrations, long run-queue).
func makeWorkers() []Worker {
	workers := make([]Worker, 32)
	for w := 0; w < 32; w++ {
		cpu := (w*7 + 4) % 64
		if w == 27 {
			cpu = 36
		}
		numa := cpu / 16
		if w == 27 {
			numa = 2
		}
		migrations := (w * 13) % 34
		if w == 27 {
			migrations = 142
		}
		runq := 0.8 + float64(w%7)*0.4
		if w == 27 {
			runq = 8.6
		}
		workers[w] = Worker{Name: fmt.Sprintf("worker-%02d", w), CPU: cpu, NUMA: numa, Migrations: migrations, RunQMS: runq}
	}
	return workers
}
