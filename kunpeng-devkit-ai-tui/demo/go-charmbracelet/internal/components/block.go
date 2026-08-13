package components

import (
	"strings"
	"unicode/utf8"

	"charm.land/lipgloss/v2"
	"github.com/mattn/go-runewidth"

	"devkitai/internal/theme"
)

// Block is a rectangular rendered region. Lines[i] is a styled string whose
// visible width is exactly Width cells; every cell carries an explicit
// background so the final screen never leaks the terminal's default color
// (spec §12.1 / §17.4).
type Block struct {
	Lines []string
	Width int
}

// Height returns the number of rows in the block.
func (b *Block) Height() int { return len(b.Lines) }

// blank renders n cells of canonical background.
func blank(t theme.Theme, n int) string {
	if n <= 0 {
		return ""
	}
	return t.Base().Render(strings.Repeat(" ", n))
}

// NewBlock creates an empty block: h rows of base-background blank cells.
func NewBlock(t theme.Theme, w, h int) *Block {
	b := &Block{Width: w, Lines: make([]string, h)}
	for i := range b.Lines {
		b.Lines[i] = blank(t, w)
	}
	return b
}

// Set places a styled line at row y. The line is expected to be exactly
// Width cells; it is right-padded, or clipped when too wide. Clipping never
// breaks ANSI state or the right border, even for wide CJK/emoji cells
// (spec §16).
func (b *Block) Set(t theme.Theme, y int, line string) {
	if y < 0 || y >= len(b.Lines) {
		return
	}
	width := lipgloss.Width(line)
	switch {
	case width == b.Width:
		b.Lines[y] = line
	case width < b.Width:
		b.Lines[y] = line + blank(t, b.Width-width)
	default:
		b.Lines[y] = clipWidth(line, b.Width)
	}
}

// clipWidth truncates a styled string to at most maxW visible cells, keeping
// ANSI escape sequences intact (they carry no width). Wide characters that
// would cross the limit are dropped as a whole.
func clipWidth(s string, maxW int) string {
	if maxW <= 0 {
		return ""
	}
	var b strings.Builder
	width := 0
	for i := 0; i < len(s); {
		r, size := utf8.DecodeRuneInString(s[i:])
		if r == '\x1b' {
			end := ansiEscapeEnd(s, i)
			b.WriteString(s[i:end])
			i = end
			continue
		}
		w := runewidth.RuneWidth(r)
		if width+w > maxW {
			break
		}
		b.WriteRune(r)
		width += w
		i += size
	}
	return b.String()
}

// ansiEscapeEnd returns the index just past the escape sequence starting at
// s[i] (which must be ESC). Handles CSI, OSC, and lone ESC.
func ansiEscapeEnd(s string, i int) int {
	j := i + 1
	if j >= len(s) {
		return j
	}
	switch s[j] {
	case '[': // CSI: ESC [ params... final(0x40-0x7e)
		j++
		for j < len(s) && !(s[j] >= 0x40 && s[j] <= 0x7e) {
			j++
		}
		if j < len(s) {
			j++
		}
	case ']': // OSC: ESC ] ... BEL or ST (ESC \)
		j++
		for j < len(s) && s[j] != '\x07' {
			if s[j] == '\x1b' && j+1 < len(s) && s[j+1] == '\\' {
				j += 2
				return j
			}
			j++
		}
		if j < len(s) {
			j++
		}
	default:
		j++ // lone ESC or single-char sequence
	}
	return j
}

// Pad extends the block to height h with base-background blank rows.
func (b *Block) Pad(t theme.Theme, h int) {
	for len(b.Lines) < h {
		b.Lines = append(b.Lines, blank(t, b.Width))
	}
}

// Box renders a rounded-border box: border glyphs carry borderFg on the base
// background, the interior carries bg. topMid and bottomMid are styled strings
// drawn into the top (left-aligned) and bottom (right-aligned) borders —
// e.g. the "Ask DevKit AI" label and the "enter ↵" hint. content holds the
// styled interior lines; each is padded to the interior width on bg.
// Border glyphs are drawn by hand (not lipgloss .Border) so every cell gets
// an explicit background (spec §12.1).
func Box(t theme.Theme, w, h int, borderFg, bg, topMid, bottomMid string, content []string) *Block {
	return BoxBold(t, w, h, borderFg, bg, topMid, bottomMid, content, false)
}

// BoxBold is Box with an optional bold border (used for the brief empty-Enter
// emphasis pulse, spec §8.3).
func BoxBold(t theme.Theme, w, h int, borderFg, bg, topMid, bottomMid string, content []string, boldBorder bool) *Block {
	bd := lipgloss.RoundedBorder()
	borderStyle := t.Style(borderFg, t.P.BgBase)
	if boldBorder {
		borderStyle = borderStyle.Bold(true)
	}
	border := func(s string) string { return borderStyle.Render(s) }
	interior := func(s string) string { return t.Style("", bg).Render(s) }

	// Top border: ╭ ─ label ────── ╮ (label in its own style; the dashes and
	// padding are border cells on the base background).
	topMidW := lipgloss.Width(topMid)
	fill := w - 1 - 2 - topMidW - 1 - 1
	if fill < 1 {
		fill = 1
	}
	top := border(bd.TopLeft) + border(bd.Top+" ") + topMid + border(" "+strings.Repeat(bd.Top, fill)) + border(bd.TopRight)

	inner := make([]string, h-2)
	for i := 0; i < h-2; i++ {
		var c string
		if i < len(content) {
			c = content[i]
		}
		cw := lipgloss.Width(c)
		var pad string
		if cw < w-2 {
			pad = strings.Repeat(" ", (w-2)-cw)
		}
		inner[i] = border(bd.Left) + interior(c+pad) + border(bd.Right)
	}

	// Bottom border: ╰ ────── enter ↵ ─ ╯ (hint right-aligned before the
	// corner). With no hint the border is a plain run of dashes.
	var bottom string
	if bottomMid != "" {
		bottomMidW := lipgloss.Width(bottomMid)
		bfill := w - 1 - bottomMidW - 1 - 1 - 1
		if bfill < 1 {
			bfill = 1
		}
		bottom = border(bd.BottomLeft) + border(strings.Repeat(bd.Bottom, bfill)) + border(" ") + bottomMid + border(bd.Bottom) + border(bd.BottomRight)
	} else {
		bottom = border(bd.BottomLeft) + border(strings.Repeat(bd.Bottom, w-2)) + border(bd.BottomRight)
	}

	lines := make([]string, 0, h)
	lines = append(lines, top)
	lines = append(lines, inner...)
	lines = append(lines, bottom)

	blk := NewBlock(t, w, h)
	for i, ln := range lines {
		blk.Set(t, i, ln)
	}
	return blk
}

// ComposeScreen lays the content block onto a full w×h screen at the given
// top-left offset (cells outside the block stay canonical background) and
// returns the final multi-line styled string, one line per terminal row.
func ComposeScreen(t theme.Theme, w, h, contentX, contentY int, content *Block) string {
	rows := make([]string, h)
	for y := range rows {
		if y >= contentY && y < contentY+content.Height() {
			pad := w - contentX - content.Width
			if pad < 0 {
				pad = 0
			}
			rows[y] = blank(t, contentX) + content.Lines[y-contentY] + blank(t, pad)
		} else {
			rows[y] = blank(t, w)
		}
	}
	return strings.Join(rows, "\n")
}

// JoinH top-aligns blocks horizontally, separating them with base-background
// gap columns. The result is one block whose width is the sum of the inputs.
func JoinH(t theme.Theme, gap int, blocks ...*Block) *Block {
	if len(blocks) == 0 {
		return NewBlock(t, 0, 0)
	}
	width := 0
	height := 0
	for _, b := range blocks {
		width += b.Width
		if b.Height() > height {
			height = b.Height()
		}
	}
	if len(blocks) > 1 {
		width += gap * (len(blocks) - 1)
	}
	out := NewBlock(t, width, height)
	for y := 0; y < height; y++ {
		var sb strings.Builder
		for i, b := range blocks {
			if y < b.Height() {
				sb.WriteString(b.Lines[y])
			} else {
				sb.WriteString(blank(t, b.Width))
			}
			if i < len(blocks)-1 {
				sb.WriteString(blank(t, gap))
			}
		}
		out.Lines[y] = sb.String()
	}
	return out
}

// JoinV stacks blocks vertically, left-aligned; narrower blocks are padded
// with base-background cells to the widest block. gap blank rows separate
// consecutive blocks.
func JoinV(t theme.Theme, gap int, blocks ...*Block) *Block {
	if len(blocks) == 0 {
		return NewBlock(t, 0, 0)
	}
	width := 0
	height := 0
	for _, b := range blocks {
		if b.Width > width {
			width = b.Width
		}
		height += b.Height()
	}
	if len(blocks) > 1 {
		height += gap * (len(blocks) - 1)
	}
	out := NewBlock(t, width, height)
	y := 0
	for i, b := range blocks {
		for j, ln := range b.Lines {
			out.Lines[y+j] = ln + blank(t, width-b.Width)
		}
		y += b.Height()
		if i < len(blocks)-1 {
			y += gap
		}
	}
	return out
}
