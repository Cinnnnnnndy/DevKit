package dashboard

import (
	"strings"
	"testing"

	"charm.land/lipgloss/v2"
	"github.com/charmbracelet/x/ansi"

	"devkitai/internal/theme"
)

func testTheme() theme.Theme {
	return theme.Theme{P: theme.Default, NoColor: false}
}

func constValues(n int, v float64) []float64 {
	out := make([]float64, n)
	for i := range out {
		out[i] = v
	}
	return out
}

func TestBrailleLineConstant(t *testing.T) {
	// A constant series has no vertical spread → all cells empty, but the
	// rows stay exactly w cells wide with the cursor column present.
	rows := brailleLine(constValues(SampleCount, 50), 40, 4, 20)
	if len(rows) != 4 {
		t.Fatalf("rows = %d, want 4", len(rows))
	}
	for _, r := range rows {
		if ansi.StringWidth(r) != 40 {
			t.Errorf("row width = %d, want 40 (%q)", ansi.StringWidth(r), r)
		}
		if !strings.Contains(r, "│") {
			t.Error("cursor column missing")
		}
	}
}

func TestBrailleLineWidths(t *testing.T) {
	s := NewSession()
	rows := brailleLine(s.CPU, 109, 4, 50)
	for i, r := range rows {
		if ansi.StringWidth(r) != 109 {
			t.Errorf("row %d width = %d, want 109", i, ansi.StringWidth(r))
		}
	}
}

func TestBrailleAreaFills(t *testing.T) {
	s := NewSession()
	// invert=false fills from the bottom edge: the last row must contain dots.
	bottom := brailleArea(s.RemoteNUMA, 30, 3, 15, false)
	last := strings.ReplaceAll(bottom[2], " ", "")
	if last == "" {
		t.Error("invert=false area should fill the bottom row")
	}
	// invert=true fills from the top edge: the first row must contain dots.
	top := brailleArea(s.RemoteNUMA, 30, 3, 15, true)
	first := strings.ReplaceAll(top[0], " ", "")
	if first == "" {
		t.Error("invert=true area should fill the top row")
	}
}

func TestBrailleRowStyledCursor(t *testing.T) {
	tt := testTheme()
	styled := brailleRowStyled(tt, colBlue, brailleLine(constValues(SampleCount, 50), 9, 1, 2)[0], 2)
	if !strings.Contains(styled, "│") {
		t.Error("styled row should contain the cursor glyph")
	}
	if ansi.StringWidth(styled) != 9 {
		t.Errorf("styled width = %d, want 9", ansi.StringWidth(styled))
	}
}

func TestHeatmapRows(t *testing.T) {
	tt := testTheme()
	s := NewSession()
	core := s.CoreUtil[SampleCount-1]
	nodes := s.NodeUtil[SampleCount-1]
	rows := heatmap(tt, core, nodes, 42)
	if len(rows) != 8 {
		t.Fatalf("rows = %d, want 8 (legend, blank, 4 cores, blank, hotspot)", len(rows))
	}
	for i, r := range rows {
		if w := lipgloss.Width(r); w > 42 {
			t.Errorf("row %d width = %d, want <=42 (%q)", i, w, r)
		}
	}
	// The hot core callout references core 34-38 (the migration hotspot).
	if !strings.Contains(rows[7], "cross-NUMA hotspot") {
		t.Errorf("hotspot row missing: %q", rows[7])
	}
}

func TestSegmentedGauge(t *testing.T) {
	tt := testTheme()
	rows := segmentedGauge(tt, 21.0, 64)
	for i, r := range rows {
		if w := lipgloss.Width(r); w > 64 {
			t.Errorf("row %d width = %d, want <=64", i, w)
		}
	}
	joined := strings.Join(rows, "\n")
	for _, token := range []string{"used", "cached", "kv", "free", "REMOTE PAGE PRESSURE"} {
		if !strings.Contains(joined, token) {
			t.Errorf("gauge missing %q", token)
		}
	}
}

func TestOperatorRaceCrossing(t *testing.T) {
	tt := testTheme()
	s := NewSession()
	// At the latest sample attention_fwd leads the race.
	rows := operatorRace(tt, s, SampleCount-1, 42)
	if len(rows) != 4 {
		t.Fatalf("rows = %d, want 4", len(rows))
	}
	if !strings.HasPrefix(ansi.Strip(rows[0]), "01 attention_fwd") {
		t.Errorf("latest-sample leader = %q, want attention_fwd", ansi.Strip(rows[0]))
	}
	if !strings.Contains(rows[3], "attention overtook matmul") {
		t.Errorf("footer missing migration note: %q", rows[3])
	}
	for i, r := range rows {
		if w := lipgloss.Width(r); w > 42 {
			t.Errorf("row %d width = %d, want <=42", i, w)
		}
	}
}

func TestHeroNumber(t *testing.T) {
	got := heroNumber("184")
	want := [3]string{
		" ▄█ █▀█ █ █",
		"  █ █▀█ ▀▀█",
		" ▄█ █▄█   █",
	}
	if got != want {
		t.Errorf("hero 184:\n got %q\nwant %q", got, want)
	}
}

func TestKPIValue(t *testing.T) {
	if got := kpiValue(184.2, 0); got != "184" {
		t.Errorf("kpiValue(184.2,0) = %s, want 184", got)
	}
	if got := kpiValue(42.78, 1); got != "42.8" {
		t.Errorf("kpiValue(42.78,1) = %s, want 42.8", got)
	}
}
