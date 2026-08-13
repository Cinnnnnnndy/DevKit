// Package layout computes the Launch page geometry. Metrics is the single
// source of truth for both rendering and mouse hit-testing, so click and
// render can never disagree (spec §18.3).
package layout

import "devkitai/internal/components"

// Tier selects the layout regime (spec §4).
type Tier int

const (
	TierTooSmall Tier = iota // w<72 or h<24: size page
	TierSingle               // 72 <= w < 112: single column
	TierDual                 // w >= 112: two columns
)

// Rect is a rectangle in terminal coordinates (cells).
type Rect struct{ X, Y, W, H int }

// Metrics holds the computed geometry for the current viewport.
type Metrics struct {
	Tier Tier
	W, H int // full terminal size

	CX, CY int // content origin
	CW, CH int // content size

	LeftW, Gap, RightW int // dual-column split

	Tight bool // single column with a short viewport: gaps removed, resume 1-row

	PromptRect       Rect
	FeedbackRect     Rect
	ActionsLabelRect Rect
	ActionRects      [3]Rect
	StatusRect       Rect
	HelpRect         Rect
}

// Metrics computes the layout for the given viewport.
func Compute(w, h int) Metrics {
	m := Metrics{W: w, H: h, LeftW: components.BrandWidth}

	if w < 72 || h < 24 {
		m.Tier = TierTooSmall
		return m
	}

	if w >= 112 {
		m.Tier = TierDual
		if w >= 128 {
			m.Gap = 6
		} else {
			m.Gap = 4
		}
		m.CW = min(104, w-2)
		m.RightW = m.CW - m.LeftW - m.Gap
		if m.RightW < 40 {
			m.RightW = 40
		}
		m.CH = 20
	} else {
		m.Tier = TierSingle
		m.RightW = min(68, w-4)
		m.CW = m.RightW
		m.CH = 22
		m.Tight = h < 26
		if m.Tight {
			m.CH = 15
		}
	}

	m.CX = (w - m.CW) / 2
	m.CY = (h - m.CH) / 2
	if m.Tier == TierDual {
		m.CY-- // visual centering may sit 1-2 rows above the math center (§4.1)
	}
	if m.CY < 1 {
		m.CY = 1
	}

	m.layoutColumn()
	return m
}

// layoutColumn computes the per-region rects of the interactive column.
func (m *Metrics) layoutColumn() {
	rightX := m.CX
	if m.Tier == TierDual {
		rightX = m.CX + m.LeftW + m.Gap
	}
	gap := 1
	if m.Tight {
		gap = 0
	}

	y := m.CY
	if m.Tier == TierSingle {
		y += 1 // compact brand line
		y += gap
	}

	m.PromptRect = Rect{rightX, y, m.RightW, 3}
	y += 3 + gap

	m.FeedbackRect = Rect{rightX, y, m.RightW, 1}
	y += 1 + gap

	m.ActionsLabelRect = Rect{rightX, y, m.RightW, 1}
	y += 1 + gap

	// action items: 2 rows each + 1 gap row between (resume collapses to 1
	// row in tight layouts)
	actionsY := y
	heights := [3]int{2, 2, 2}
	if m.Tight {
		heights[2] = 1
	}
	yy := actionsY
	for i := 0; i < 3; i++ {
		m.ActionRects[i] = Rect{rightX, yy, m.RightW, heights[i]}
		yy += heights[i]
		if i < 2 {
			yy++
		}
	}
	y = yy + gap

	m.StatusRect = Rect{rightX, y, m.RightW, 1}
	y += 1 + gap

	m.HelpRect = Rect{rightX, y, m.RightW, 1}
}

// ActionAt returns the index of the action item covering point (x, y), or -1.
// Coordinates are absolute terminal cells (0,0 top-left), matching mouse
// events.
func (m Metrics) ActionAt(x, y int) int {
	for i, r := range m.ActionRects {
		if x >= r.X && x < r.X+r.W && y >= r.Y && y < r.Y+r.H {
			return i
		}
	}
	return -1
}

// PromptAt reports whether the point lies inside the prompt box.
func (m Metrics) PromptAt(x, y int) bool {
	r := m.PromptRect
	return x >= r.X && x < r.X+r.W && y >= r.Y && y < r.Y+r.H
}
