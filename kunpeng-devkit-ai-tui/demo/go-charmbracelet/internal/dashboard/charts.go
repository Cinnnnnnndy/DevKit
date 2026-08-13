package dashboard

import (
	"fmt"
	"math"
	"strings"

	"devkitai/internal/theme"
)

// Chart series colors (ported from Scheme A's semantic map, spec.md §L332-338):
// time-series blue, NUMA/memory accum-orange, CPU green, danger pink. They are
// dashboard-local constants, applied through t.Style so NO_COLOR degrades to
// symbol-only rendering automatically.
const (
	colBlue     = "#3c7cf6"
	colCyan     = "#01a7ba"
	colGreen    = "#04d793"
	colViolet   = "#5f3cff"
	colMagenta  = "#ab43ab"
	colOrange   = "#ffaa3b"
	colOrange2  = "#d9862c"
	colOrangeBg = "#4a2d17"
	colPink     = "#ff4b7b"
	colAccent   = "#3d98ff"
)

// sparkBlocks is the 8-level block density ramp for heatmaps and gauges.
const sparkBlocks = "▁▂▃▄▅▆▇█"

// heatRamp is the 5-step accum-orange scale for core utilization.
var heatRamp = []string{"#4a2d17", "#70411d", "#9b5422", "#d9862c", "#ffc777"}

func minF(values ...float64) float64 {
	m := values[0]
	for _, v := range values[1:] {
		if v < m {
			m = v
		}
	}
	return m
}
func maxF(values ...float64) float64 {
	m := values[0]
	for _, v := range values[1:] {
		if v > m {
			m = v
		}
	}
	return m
}

// ---------------------------------------------------------------- braille --

// brailleLine renders one series as an h×w braille history (each cell is a
// 2×4-dot glyph). It returns plain rows; the cursor column is a "│" that the
// caller styles distinctly. Mirrors Scheme A's braille_line.
func brailleLine(values []float64, w, h, cursorX int) []string {
	if w <= 0 || h <= 0 || len(values) == 0 {
		return nil
	}
	pw, ph := w*2, h*4
	low, high := minF(values...), maxF(values...)
	scale := math.Max(1.0, high-low)
	cells := make([][]uint8, h)
	for i := range cells {
		cells[i] = make([]uint8, w)
	}
	prevX, prevY := -1, 0
	for px := 0; px < pw; px++ {
		idx := int(math.Round(float64(px) / float64(maxInt(1, pw-1)) * float64(len(values)-1)))
		py := ph - 1 - int(math.Round((values[idx]-low)/scale*float64(ph-1)))
		if prevX >= 0 {
			dist := maxInt(1, absInt(py-prevY))
			for step := 1; step < dist; step++ {
				setDot(cells, px, prevY+(py-prevY)*step/dist)
			}
		}
		setDot(cells, px, py)
		prevX, prevY = px, py
	}
	return brailleRows(cells, w, cursorX)
}

// brailleArea renders a filled area, growing up from the bottom edge or (when
// invert) down from the top edge. Mirrors Scheme A's braille_area.
func brailleArea(values []float64, w, h, cursorX int, invert bool) []string {
	if w <= 0 || h <= 0 || len(values) == 0 {
		return nil
	}
	pw, ph := w*2, h*4
	low, high := minF(values...), maxF(values...)
	scale := math.Max(1.0, high-low)
	cells := make([][]uint8, h)
	for i := range cells {
		cells[i] = make([]uint8, w)
	}
	for px := 0; px < pw; px++ {
		idx := int(math.Round(float64(px) / float64(maxInt(1, pw-1)) * float64(len(values)-1)))
		extent := int(math.Round((values[idx] - low) / scale * float64(ph-1)))
		y0, y1 := ph-1-extent, ph-1
		if invert {
			y0, y1 = 0, extent
		}
		for py := y0; py <= y1; py++ {
			setDot(cells, px, py)
		}
	}
	return brailleRows(cells, w, cursorX)
}

// setDot ORs the braille dot at pixel (px,py) into the cell grid.
func setDot(cells [][]uint8, px, py int) {
	h := len(cells) * 4
	if py < 0 {
		py = 0
	}
	if py >= h {
		py = h - 1
	}
	cx, dx := px/2, px%2
	cy, dy := py/4, py%4
	dots := [2][4]uint8{{0x01, 0x02, 0x04, 0x40}, {0x08, 0x10, 0x20, 0x80}}
	cells[cy][cx] |= dots[dx][dy]
}

func brailleRows(cells [][]uint8, w, cursorX int) []string {
	lines := make([]string, len(cells))
	for row, bits := range cells {
		var b strings.Builder
		b.Grow(w)
		for col := 0; col < w; col++ {
			if col == cursorX {
				b.WriteString("│")
			} else if bits[col] != 0 {
				b.WriteRune(rune(0x2800 + int(bits[col])))
			} else {
				b.WriteString(" ")
			}
		}
		lines[row] = b.String()
	}
	return lines
}

// brailleRowStyled styles one plain braille row: track-colored cells except
// the cursor column, which renders in the secondary color so the shared
// vertical cursor reads as one line across all tracks.
func brailleRowStyled(t theme.Theme, color, plain string, cursorX int) string {
	runes := []rune(plain)
	if cursorX >= 0 && cursorX < len(runes) {
		var b strings.Builder
		if cursorX > 0 {
			b.WriteString(t.Style(color, "").Render(string(runes[:cursorX])))
		}
		b.WriteString(t.Style(t.P.TextSecondary, "").Render("│"))
		if cursorX+1 < len(runes) {
			b.WriteString(t.Style(color, "").Render(string(runes[cursorX+1:])))
		}
		return b.String()
	}
	return t.Style(color, "").Render(plain)
}

func absInt(a int) int {
	if a < 0 {
		return -a
	}
	return a
}

// ----------------------------------------------------------------- heatmap --

// heatmap renders the 4×16 core utilization grid (64 cores, never collapsed to
// NUMA aggregates per spec) with the accum-orange ramp, per-row NUMA gauges and
// a hot-core callout. Returns styled lines; each is ≤ w cells.
func heatmap(t theme.Theme, core []int, nodes []int, w int) []string {
	var out []string
	out = append(out, t.Muted().Render("▁0  ▃20  ▅40  ▇60  █80–100"))
	out = append(out, "")

	for row := 0; row < 4; row++ {
		var b strings.Builder
		b.WriteString(t.Muted().Render(fmt.Sprintf("%02d–%02d  ", row*16, row*16+15)))
		for c := 0; c < 16; c++ {
			v := core[row*16+c]
			ch := string(sparkBlocks[minInt(7, v/13)])
			b.WriteString(t.Style(heatRamp[minInt(4, v/20)], "").Render(ch))
		}
		b.WriteString(t.Muted().Render(fmt.Sprintf("   N%d ", row)))
		g := int(math.Round(float64(nodes[row]) / 100 * 6))
		b.WriteString(t.Style(colOrange2, "").Render(strings.Repeat("█", g)))
		b.WriteString(t.Style(colOrangeBg, "").Render(strings.Repeat("░", 6-g)))
		b.WriteString(t.Secondary().Render(fmt.Sprintf(" %02d%%", nodes[row])))
		out = append(out, b.String())
	}

	hot, hv := 0, -1
	for c, v := range core {
		if v > hv {
			hot, hv = c, v
		}
	}
	out = append(out, "")
	out = append(out, t.Style(t.P.StateDanger, "").Bold(true).Render(fmt.Sprintf("▚▚▚ core %02d  %d%% · cross-NUMA hotspot", hot, hv)))
	return out
}

// --------------------------------------------------------- segmented gauge --

// segmentedGauge renders the 64 GiB memory pressure split (used / cached / KV /
// free) with segment colors AND numeric labels coexisting, plus the remote
// page pressure bar below.
func segmentedGauge(t theme.Theme, remote float64, w int) []string {
	used := 22.0 + remote*0.22
	cached := 12.0
	kv := 4.0 + remote*0.08
	free := math.Max(0, 64-used-cached-kv)
	values := []float64{used, cached, kv, free}
	colors := []string{"#ffc777", "#d9862c", "#9b5422", "#343434"}

	barW := maxInt(22, w-12)
	counts := make([]int, 4)
	for i, v := range values {
		counts[i] = int(math.Round(v / 64 * float64(barW)))
	}
	counts[3] += barW - (counts[0] + counts[1] + counts[2] + counts[3])

	var b strings.Builder
	for i, c := range counts {
		b.WriteString(t.Style(colors[i], "").Render(strings.Repeat("█", maxInt(0, c))))
	}
	b.WriteString(t.Style(t.P.TextPrimary, "").Bold(true).Render(fmt.Sprintf("  %4.1f/64G", 64-free)))

	labels := t.Secondary().Render(fmt.Sprintf("used %4.1f  cached %4.1f  kv %3.1f  free %4.1f", used, cached, kv, free))

	level := minInt(20, int(math.Round(remote/30*20)))
	pressureColor := colPink
	if remote < 20 {
		pressureColor = colOrange2
	}
	pressure := t.Muted().Render("REMOTE PAGE PRESSURE  ") +
		t.Style(pressureColor, "").Render(strings.Repeat("█", level)) +
		t.Style(colOrangeBg, "").Render(strings.Repeat("░", 20-level)) +
		t.Style(colOrange, "").Bold(true).Render(fmt.Sprintf("  %4.1f%%", remote))

	return []string{b.String(), labels, "", pressure}
}

// ---------------------------------------------------------- bidirectional --

// bidirectionalArea renders DDR local reads (top half, blue) vs remote traffic
// (bottom half, orange, inverted) sharing the time cursor column.
func bidirectionalArea(t theme.Theme, s *Session, cursor, w, h int) []string {
	local := make([]float64, SampleCount)
	remote := make([]float64, SampleCount)
	for i := 0; i < SampleCount; i++ {
		local[i] = math.Max(20, s.CPU[i]*1.55-s.RemoteNUMA[i]*0.8)
		remote[i] = s.RemoteNUMA[i] * 2.7
	}
	cursorX := int(math.Round(float64(cursor) / float64(SampleCount-1) * float64(w-1)))

	out := make([]string, 0, 1+h+h+1)
	out = append(out, t.Style(colAccent, "").Bold(true).Render(fmt.Sprintf("LOCAL  %5.1f GB/s", local[cursor])))
	for _, row := range brailleArea(local, w, h, cursorX, false) {
		out = append(out, brailleRowStyled(t, colBlue, row, cursorX))
	}
	for _, row := range brailleArea(remote, w, h, cursorX, true) {
		out = append(out, brailleRowStyled(t, colOrange, row, cursorX))
	}
	out = append(out, t.Style(colOrange, "").Bold(true).Render(fmt.Sprintf("REMOTE %5.1f GB/s  · %s", remote[cursor], s.Timestamps[cursor])))
	return out
}

// ------------------------------------------------------------- kernel race --

// operatorRace ranks the hot kernels by window share at the cursor; after the
// worker migration attention_fwd must lead matmul_4096. Shows the top 3.
func operatorRace(t theme.Theme, s *Session, cursor, w int) []string {
	progress := float64(cursor) / float64(SampleCount-1)
	remote := s.RemoteNUMA[cursor]
	scores := map[string]float64{
		"attention_fwd": 24 + progress*22 + remote*0.55,
		"matmul_4096":   37 - progress*8,
		"kv_cache_update": 12 + remote*0.75,
		"layernorm":     18 - progress*3,
	}
	ranked := make([]struct{ name string; value float64 }, 0, len(scores))
	for name, value := range scores {
		ranked = append(ranked, struct{ name string; value float64 }{name, value})
	}
	for i := 1; i < len(ranked); i++ {
		for j := i; j > 0 && ranked[j].value > ranked[j-1].value; j-- {
			ranked[j], ranked[j-1] = ranked[j-1], ranked[j]
		}
	}

	maxV := ranked[0].value
	colors := []string{colPink, colOrange, colAccent, t.P.TextMuted}
	barW := maxInt(8, w-25)

	out := make([]string, 0, 4)
	for rank := 0; rank < minInt(3, len(ranked)); rank++ {
		r := ranked[rank]
		bar := maxInt(1, int(math.Round(r.value/maxV*float64(barW))))
		line := t.Muted().Render(fmt.Sprintf("%02d %-13s ", rank+1, r.name)) +
			t.Style(colors[rank], "").Render(strings.Repeat("█", bar)) +
			t.Style(colors[rank], "").Bold(true).Render(fmt.Sprintf(" %4.1f%%", r.value))
		out = append(out, line)
	}
	out = append(out, t.Muted().Render(fmt.Sprintf("%s · attention overtook matmul", s.Timestamps[cursor])))
	return out
}

// ------------------------------------------------------------------ KPI card --

// metricCard renders a KPI card: a 1-cell tone edge + 3-row hero number +
// label + detail, all on a raised surface. width w, height 6.
func metricCard(t theme.Theme, label, value, unit, detail, tone string, w int) []string {
	hero := heroNumber(value)
	strip := t.Style("", tone).Render(" ")
	card := func(fg, s string) string { return strip + t.Style(fg, t.P.BgSurface).Render(s) }
	rows := make([]string, 0, 6)
	rows = append(rows, card(tone, hero[0]))
	rows = append(rows, card(tone, hero[1]+"  "+unit))
	rows = append(rows, card(tone, hero[2]))
	rows = append(rows, card(t.P.TextPrimary, label))
	rows = append(rows, card(t.P.TextMuted, "  "+detail))
	rows = append(rows, strip+t.Style("", t.P.BgSurface).Render(""))
	return rows
}

// kpiValue renders a cursor-linked KPI value string for a metric card.
func kpiValue(v float64, decimals int) string {
	if decimals > 0 {
		return fmt.Sprintf("%."+fmt.Sprint(decimals)+"f", v)
	}
	return fmt.Sprintf("%d", int(math.Round(v)))
}
