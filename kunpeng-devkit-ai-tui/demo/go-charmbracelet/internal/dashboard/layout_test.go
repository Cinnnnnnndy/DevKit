package dashboard

import "testing"

func TestComputeMetricsCanonical(t *testing.T) {
	m := ComputeMetrics(156, 48)
	if m.TooSmall {
		t.Fatal("156x48 should not be too small")
	}

	if m.HeaderRect != (Rect{0, 0, 156, 1}) {
		t.Errorf("header = %+v", m.HeaderRect)
	}
	if m.FooterRect != (Rect{0, 47, 156, 1}) {
		t.Errorf("footer = %+v", m.FooterRect)
	}
	if m.ContentRect != (Rect{0, 2, 156, 45}) {
		t.Errorf("content = %+v", m.ContentRect)
	}
	if m.KPIRect != (Rect{0, 2, 156, 6}) {
		t.Errorf("kpi = %+v", m.KPIRect)
	}

	want := []Rect{
		{X: 0, Y: 8, W: 111, H: 25},  // trend spans col1 + gap + col2
		{X: 112, Y: 8, W: 44, H: 25}, // heat (col3)
		{X: 0, Y: 34, W: 66, H: 13},  // gauge (col1)
		{X: 67, Y: 34, W: 44, H: 13}, // area (col2)
		{X: 112, Y: 34, W: 44, H: 13},
	}
	got := []Rect{m.TrendRect, m.HeatRect, m.GaugeRect, m.AreaRect, m.RaceRect}
	for i := range want {
		if got[i] != want[i] {
			t.Errorf("pane %d = %+v, want %+v", i, got[i], want[i])
		}
	}
	if m.TrendPlot != (Rect{1, 9, 109, 23}) {
		t.Errorf("trend plot = %+v, want {1 9 109 23}", m.TrendPlot)
	}
}

func TestComputeMetricsTooSmall(t *testing.T) {
	if m := ComputeMetrics(90, 30); !m.TooSmall {
		t.Error("90x30 should be too small")
	}
	if m := ComputeMetrics(156, 31); !m.TooSmall {
		t.Error("156x31 should be too small (h<32)")
	}
}

func TestTabs(t *testing.T) {
	m := ComputeMetrics(156, 48)
	// Each tab is label+4 wide, 1 gap apart, laid out from x=0 on row 1.
	expected := []struct {
		label string
		x, w  int
	}{
		{"Overview", 0, 12}, {"CPU", 13, 7}, {"NUMA", 21, 8},
		{"Flame", 30, 9}, {"Trace", 40, 9}, {"Operators", 50, 13},
	}
	for i, e := range expected {
		r := m.TabRects[i]
		if r.X != e.x || r.W != e.w || r.Y != 1 {
			t.Errorf("tab %d (%s) rect = %+v, want x=%d w=%d y=1", i, e.label, r, e.x, e.w)
		}
		if tabLabels[i] != e.label {
			t.Errorf("tab %d label = %s, want %s", i, tabLabels[i], e.label)
		}
	}
}

func TestTabAt(t *testing.T) {
	m := ComputeMetrics(156, 48)
	if got := m.TabAt(1, 1); got != 0 {
		t.Errorf("overview hit = %d, want 0", got)
	}
	if got := m.TabAt(50, 1); got != 5 {
		t.Errorf("operators hit = %d, want 5", got)
	}
	if got := m.TabAt(0, 0); got != -1 {
		t.Errorf("header hit = %d, want -1", got)
	}
	if got := m.TabAt(100, 1); got != -1 {
		t.Errorf("gap hit = %d, want -1", got)
	}
}

func TestSampleAt(t *testing.T) {
	m := ComputeMetrics(156, 48)
	plot := m.TrendPlot // {1, 9, 109, 23}
	// Left edge → sample 0, right edge → 119, middle → ~59.
	if got := m.SampleAt(plot, plot.X); got != 0 {
		t.Errorf("left = %d, want 0", got)
	}
	if got := m.SampleAt(plot, plot.X+plot.W-1); got != SampleCount-1 {
		t.Errorf("right = %d, want %d", got, SampleCount-1)
	}
	if got := m.SampleAt(plot, plot.X+plot.W/2); got < 55 || got > 64 {
		t.Errorf("middle = %d, want ~60", got)
	}
	// Clamping: out-of-range x resolves to the nearest edge.
	if got := m.SampleAt(plot, -10); got != 0 {
		t.Errorf("far left clamp = %d, want 0", got)
	}
	if got := m.SampleAt(plot, 999); got != SampleCount-1 {
		t.Errorf("far right clamp = %d, want 119", got)
	}
}

func TestRectContains(t *testing.T) {
	r := Rect{1, 9, 109, 23}
	cases := []struct {
		x, y int
		want bool
	}{
		{1, 9, true}, {109, 31, true}, {0, 9, false}, {110, 9, false}, {1, 8, false},
	}
	for _, c := range cases {
		if got := r.Contains(c.x, c.y); got != c.want {
			t.Errorf("contains(%d,%d) = %v, want %v", c.x, c.y, got, c.want)
		}
	}
}
