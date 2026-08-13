package dashboard

import (
	"reflect"
	"testing"
)

// The demo capture must be deterministic and tell the same story as Scheme A:
// a worker migration after sample 72 drives remote-NUMA up to ~21% and P99 up
// to ~184ms while cores 34–38 go hot.
func TestSessionDeterministic(t *testing.T) {
	a := NewSession()
	b := NewSession()
	if !reflect.DeepEqual(a, b) {
		t.Fatal("NewSession() is not deterministic")
	}
}

func TestSessionShapes(t *testing.T) {
	s := NewSession()
	if len(s.Timestamps) != SampleCount {
		t.Errorf("timestamps = %d, want %d", len(s.Timestamps), SampleCount)
	}
	if len(s.CoreUtil) != SampleCount || len(s.CoreUtil[0]) != 64 {
		t.Errorf("core utilization shape = %dx%d, want 120x64", len(s.CoreUtil), len(s.CoreUtil[0]))
	}
	if len(s.NodeUtil) != SampleCount || len(s.NodeUtil[0]) != 4 {
		t.Errorf("node utilization shape = %dx%d, want 120x4", len(s.NodeUtil), len(s.NodeUtil[0]))
	}
	if len(s.Operators) < 16 {
		t.Errorf("operators = %d, want >=16", len(s.Operators))
	}
	if len(s.FlameNodes) < 18 {
		t.Errorf("flame nodes = %d, want >=18", len(s.FlameNodes))
	}
	if len(s.TraceLanes) < 28 {
		t.Errorf("trace lanes = %d, want >=28", len(s.TraceLanes))
	}
	if len(s.Workers) < 32 {
		t.Errorf("workers = %d, want >=32", len(s.Workers))
	}
}

func TestSessionStory(t *testing.T) {
	s := NewSession()
	// remote NUMA ends near 21% (migration happened).
	if got := s.RemoteNUMA[SampleCount-1]; got < 20 || got > 22 {
		t.Errorf("RemoteNUMA[119] = %.2f, want ~21", got)
	}
	// P99 ends near 184ms (+37% regression).
	if got := s.Latency[SampleCount-1]; got < 182 || got > 186 {
		t.Errorf("Latency[119] = %.2f, want ~184", got)
	}
	// Hot cores 34–38 are clearly hotter after the migration.
	before := s.CoreUtil[71][36]
	after := s.CoreUtil[119][36]
	if after <= before {
		t.Errorf("core 36 hot: after=%d before=%d, want after>before", after, before)
	}
	if s.CoreUtil[119][36] < 60 {
		t.Errorf("core 36 at 119 = %d, want hot (>60)", s.CoreUtil[119][36])
	}
	// Remote NUMA starts low (~5%) and rises.
	if s.RemoteNUMA[0] > 7 {
		t.Errorf("RemoteNUMA[0] = %.2f, want ~5", s.RemoteNUMA[0])
	}
}

func TestSessionTimestamps(t *testing.T) {
	s := NewSession()
	if s.Timestamps[0] != "14:32:00" {
		t.Errorf("first timestamp = %q, want 14:32:00", s.Timestamps[0])
	}
	if s.Timestamps[SampleCount-1] != "14:37:57" {
		t.Errorf("last timestamp = %q, want 14:37:57", s.Timestamps[SampleCount-1])
	}
}

func TestSessionEvents(t *testing.T) {
	s := NewSession()
	want := []Event{
		{57, "candidate-42 deployed", "info"},
		{72, "worker-27 migrated N0 → N2", "warning"},
		{78, "remote memory crossed 20%", "danger"},
		{88, "P99 regression alert +37%", "danger"},
	}
	if !reflect.DeepEqual(s.Events, want) {
		t.Errorf("events mismatch:\n got %+v\nwant %+v", s.Events, want)
	}
}

func TestOperatorRaceCrossing(t *testing.T) {
	// attention_fwd must overtake matmul_4096 after the migration.
	s := NewSession()
	score := func(o Operator, s *Session, cursor int) float64 {
		progress := float64(cursor) / float64(SampleCount-1)
		remote := s.RemoteNUMA[cursor]
		switch o.Name {
		case "attention_fwd":
			return 24 + progress*22 + remote*0.55
		case "matmul_4096":
			return 37 - progress*8
		case "kv_cache_update":
			return 12 + remote*0.75
		case "layernorm":
			return 18 - progress*3
		}
		return 0
	}
	att := score(s.Operators[0], s, 0)
	mat := score(s.Operators[1], s, 0)
	if att >= mat {
		t.Fatalf("at sample 0 attention(%.1f) should trail matmul(%.1f)", att, mat)
	}
	att = score(s.Operators[0], s, 119)
	mat = score(s.Operators[1], s, 119)
	if att <= mat {
		t.Errorf("at sample 119 attention(%.1f) should beat matmul(%.1f)", att, mat)
	}
}
