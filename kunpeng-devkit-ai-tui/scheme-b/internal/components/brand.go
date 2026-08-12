package components

import (
	"strings"

	"devkitai/internal/theme"
)

// The Kunpeng two-tone mark, transcribed byte-for-byte from web/demo.html
// (spec §7.1: that source is the sole structural authority). Red upper-left
// wing (#ED1C24) rows 1–8, gray lower-right wing (#C9C9C9) rows 9–13; rows 3
// and 5 carry an interior plain space between the runs. Rows are tapered
// (max 33 cells); the block pads them to a common width.
type markRow struct {
	lead int
	red  string
	gray string
	mid  bool // interior plain space between red and gray
}

var markRows = []markRow{
	{31, "▄▄", "", false},
	{26, "▄▄▄█▀▀", "▄", false},
	{21, "▄▄▄███▀", "▄█▀", true},
	{15, "▄▄▄█████▀▀", "▄▄██▀", false},
	{10, "▄▄▄███████▀", "▄████▀", true},
	{7, "▄████████▀▀", "▄▄█████▀", false},
	{1, "▄▄▄▄▄▄██████▀▀", "▄▄██████▀", false},
	{3, "▀▀████▀▀", "▄▄████████▀", false},
	{9, "", "▄█████████▀", false},
	{11, "", "▀▀███████▄", false},
	{15, "", "▀▀████▄", false},
	{19, "", "▀▀██▄", false},
	{23, "", "▀▀", false},
}

// BrandWidth is the fixed width of the brand column: the mark's natural width
// (spec §4.2 grid says 28, but the mark itself is 33 cells — we keep the mark
// accurate and trim the right column instead, per §7.1 accuracy over the
// nominal grid).
const BrandWidth = 33

// fullMark renders the 13-row two-tone mark as styled lines (each line is
// exactly BrandWidth cells when placed into a block).
func fullMark(t theme.Theme) []string {
	lines := make([]string, len(markRows))
	for i, r := range markRows {
		line := blank(t, r.lead)
		if r.red != "" {
			line += t.Style(t.P.Brand, "").Render(r.red)
		}
		if r.mid {
			line += blank(t, 1)
		}
		if r.gray != "" {
			line += t.Style(t.P.BrandMarkSecondary, "").Render(r.gray)
		}
		lines[i] = line
	}
	return lines
}

// FullBrand renders the wide brand block: the 13-row mark, the bold uppercase
// wordmark (regular terminal glyphs, not the Scheme A dot-matrix font — spec
// §6.2), and the ARM64 READY capsule. Height 18, width BrandWidth.
func FullBrand(t theme.Theme) *Block {
	blk := NewBlock(t, BrandWidth, 18)
	for i, ln := range fullMark(t) {
		blk.Set(t, i, ln)
	}
	blk.Set(t, 14, t.Style(t.P.TextPrimary, "").Bold(true).Render("KUNPENG"))
	blk.Set(t, 15, t.Style(t.P.TextPrimary, "").Bold(true).Render("DEVKIT AI"))

	dot := t.Style(t.P.StateSuccess, t.P.BgSurface).Render("●")
	rest := t.Style(t.P.TextSecondary, t.P.BgSurface).Render(" ARM64 READY ")
	blk.Set(t, 17, " "+dot+rest)
	return blk
}

// CompactMark samples the full mark onto a single row by vertical projection:
// a column shows ▀ (red) if any red row covers it, ▄ (gray) if only gray rows
// cover it, and █ (red) if both — an explicit pixel-grid resample, not a
// freehand redraw (spec §7.1). Leading/trailing empty columns are trimmed.
func CompactMark(t theme.Theme) string {
	var reds, grays [BrandWidth]bool
	for _, r := range markRows {
		x := r.lead
		for range r.red {
			reds[x] = true
			x++
		}
		if r.mid {
			x++
		}
		for range r.gray {
			grays[x] = true
			x++
		}
	}
	first, last := -1, -1
	for i := 0; i < BrandWidth; i++ {
		if reds[i] || grays[i] {
			if first < 0 {
				first = i
			}
			last = i
		}
	}
	if first < 0 {
		return ""
	}
	var sb strings.Builder
	for i := first; i <= last; i++ {
		switch {
		case reds[i] && grays[i]:
			sb.WriteString(t.Style(t.P.Brand, "").Render("█"))
		case reds[i]:
			sb.WriteString(t.Style(t.P.Brand, "").Render("▀"))
		default:
			sb.WriteString(t.Style(t.P.BrandMarkSecondary, "").Render("▄"))
		}
	}
	return sb.String()
}
