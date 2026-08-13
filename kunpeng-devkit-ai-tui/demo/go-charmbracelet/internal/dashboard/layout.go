package dashboard

import (
	"math"
)

// Rect is an axis-aligned region in absolute terminal cells (0,0 top-left).
type Rect struct{ X, Y, W, H int }

// tabLabels are the fixed tab order shared by the tab bar, layout and hit
// testing (spec.md: Overview → CPU → NUMA → Flame → Trace → Operators).
var tabLabels = []string{"Overview", "CPU", "NUMA", "Flame", "Trace", "Operators"}

// TabCount is the number of tabs in the workspace.
const TabCount = 6

// Metrics is the single source of truth for the workspace geometry — both the
// View (rendering) and mouse hit-testing read from it (mirrors the Launch
// layout.Metrics pattern), so clicks and paint never drift apart.
type Metrics struct {
	W, H int

	HeaderRect Rect
	TabRects   [TabCount]Rect
	ContentRect Rect
	FooterRect Rect

	KPIRect   Rect
	TrendRect Rect // 4-track braille history pane (box)
	TrendPlot Rect // box interior: time axis used for cursor hit-testing
	HeatRect  Rect
	GaugeRect Rect
	AreaRect  Rect // DDR dual area pane (box)
	AreaPlot  Rect
	RaceRect  Rect

	TooSmall bool
}

// ComputeMetrics lays out the workspace for the given terminal size. The
// canonical 156×48 case maps to: header row 0, tab bar row 1, content rows
// 2..h-2, footer row h-1; the Overview grid is KPI strip + a 3fr/2fr/2fr ×
// 2fr/1fr main grid.
func ComputeMetrics(w, h int) Metrics {
	m := Metrics{W: w, H: h}
	if w < 100 || h < 32 {
		m.TooSmall = true
		return m
	}

	m.HeaderRect = Rect{0, 0, w, 1}
	m.FooterRect = Rect{0, h - 1, w, 1}
	m.ContentRect = Rect{0, 2, w, h - 3}
	computeTabRects(&m)

	kpiH := 6
	m.KPIRect = Rect{0, 2, w, kpiH}

	mainY := 2 + kpiH
	mainH := h - 3 - kpiH // content minus KPI strip

	gap := 1
	usable := w - 2*gap
	c1 := usable * 3 / 7
	c2 := usable * 2 / 7
	c3 := w - 2*gap - c1 - c2

	rGap := 1
	r1 := (mainH - rGap) * 2 / 3
	r2 := mainH - rGap - r1

	m.TrendRect = Rect{0, mainY, c1 + gap + c2, r1}
	m.HeatRect = Rect{c1 + gap + c2 + gap, mainY, c3, r1}
	m.GaugeRect = Rect{0, mainY + r1 + rGap, c1, r2}
	m.AreaRect = Rect{c1 + gap, mainY + r1 + rGap, c2, r2}
	m.RaceRect = Rect{c1 + gap + c2 + gap, mainY + r1 + rGap, c3, r2}

	m.TrendPlot = inset(m.TrendRect, 1)
	m.AreaPlot = inset(m.AreaRect, 1)
	return m
}

func computeTabRects(m *Metrics) {
	x := 0
	for i, label := range tabLabels {
		w := len(label) + 4
		m.TabRects[i] = Rect{x, 1, w, 1}
		x += w + 1
	}
}

func inset(r Rect, n int) Rect {
	return Rect{r.X + n, r.Y + n, r.W - 2*n, r.H - 2*n}
}

// Contains reports whether (x,y) is inside the rect (upper-left inclusive,
// lower-right exclusive, matching terminal cell coordinates).
func (r Rect) Contains(x, y int) bool {
	return x >= r.X && x < r.X+r.W && y >= r.Y && y < r.Y+r.H
}

// TabAt returns the tab index under (x,y), or -1 when none.
func (m Metrics) TabAt(x, y int) int {
	for i, r := range m.TabRects {
		if y == r.Y && x >= r.X && x < r.X+r.W {
			return i
		}
	}
	return -1
}

// SampleAt maps an x column inside a time-linked plot to a sample index
// (0..SampleCount-1). x outside the plot is clamped to the nearest edge, so
// clicks slightly past a chart still resolve; the caller decides whether the
// point is inside the plot at all.
func (m Metrics) SampleAt(r Rect, x int) int {
	if r.W <= 1 {
		return -1
	}
	px := x - r.X
	if px < 0 {
		px = 0
	}
	if px > r.W-1 {
		px = r.W - 1
	}
	return int(math.Round(float64(px) / float64(r.W-1) * float64(SampleCount-1)))
}
