package app

import (
	"flag"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"charm.land/bubbletea/v2"
	"github.com/charmbracelet/x/ansi"

)

var update = flag.Bool("update", false, "regenerate golden files")

var goldenSizes = []struct {
	w, h int
	name string
}{
	{156, 48, "launch_156x48"},
	{120, 36, "launch_120x36"},
	{100, 32, "launch_100x32"},
	{80, 24, "launch_80x24"},
	{68, 20, "launch_68x20"},
}

// launchedModel starts a model and lets it settle at the given viewport (the
// window-size message reconciles the input width and placeholder).
func launchedModel(w, h int) Model {
	m := New(true)
	m = apply(m, tea.WindowSizeMsg{Width: w, Height: h})
	return m
}

// assertFullWidth verifies every rendered line is exactly w visible cells —
// the spec's "no overflow, no border breakage" invariant (§18.2/§16).
func assertFullWidth(t *testing.T, w int, s string) {
	t.Helper()
	lines := strings.Split(s, "\n")
	if len(lines) != w && len(lines) != w+1 { // w rows; allow a trailing split artifact
	}
	for i, ln := range lines {
		if got := ansi.StringWidth(ln); got != w {
			t.Errorf("line %d width = %d, want %d", i, got, w)
		}
	}
}

func goldenPath(name string) string {
	return filepath.Join("..", "..", "testdata", "golden", name+".txt")
}

func TestGolden(t *testing.T) {
	for _, sz := range goldenSizes {
		t.Run(sz.name, func(t *testing.T) {
			m := launchedModel(sz.w, sz.h)
			got := m.render()
			assertFullWidth(t, sz.w, got)
			path := goldenPath(sz.name)
			if *update {
				if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(path, []byte(got), 0o644); err != nil {
					t.Fatal(err)
				}
				return
			}
			want, err := os.ReadFile(path)
			if err != nil {
				t.Fatalf("read golden %s: %v (run with -update)", path, err)
			}
			if string(want) != got {
				t.Errorf("golden mismatch for %s (run with -update)", sz.name)
			}
		})
	}
}

// TestGoldenNoColor asserts the NO_COLOR degradation (§5.4): no color SGR is
// emitted, yet borders, bold, symbols and the selection track survive. The
// theme (and the input's styles) must be colorless from construction.
func TestGoldenNoColor(t *testing.T) {
	t.Setenv("NO_COLOR", "1")
	m := launchedModel(156, 48)
	got := m.render()
	assertFullWidth(t, 156, got)
	if strings.Contains(got, "\x1b[38;2") || strings.Contains(got, "\x1b[48;2") {
		t.Error("NO_COLOR must not emit truecolor SGR")
	}
	if !strings.Contains(got, "\x1b[1m") {
		t.Error("NO_COLOR should keep bold for focus signals")
	}
	// Selected action track still visible: focus actions, then render.
	m = apply(m, kp("down"))
	got = m.render()
	if !strings.Contains(got, "┃") { // ┃ track char
		t.Error("selection track ┃ must survive NO_COLOR")
	}
}

// TestGoldenCJK verifies Chinese input keeps every line at full width —
// wide characters must not break the right border (spec §16).
func TestGoldenCJK(t *testing.T) {
	m := launchedModel(156, 48)
	m = apply(m, kp("将 nginx 迁移到鲲鹏 ARM64 平台"))
	got := m.render()
	assertFullWidth(t, 156, got)
	if !strings.Contains(m.input.Value(), "鲲鹏") {
		t.Fatal("CJK input should be stored")
	}
}
