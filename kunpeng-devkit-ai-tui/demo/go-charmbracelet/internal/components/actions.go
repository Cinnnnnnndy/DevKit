package components

import (
	"strings"

	"charm.land/lipgloss/v2"

	"devkitai/internal/theme"
)

// Action is a suggestion action (spec §9.1).
type Action struct {
	ID    string
	Icon  string
	Title string
	Desc  string
	Meta  string // right-aligned on the title row
}

// Actions is the fixed set of suggestion actions (spec §9.1).
var Actions = []Action{
	{ID: "migrate", Icon: "✦", Title: "Migrate a project", Desc: "Analyze dependencies and create an ARM64 plan"},
	{ID: "scan", Icon: "◇", Title: "Scan workspace", Desc: "Detect toolchains, dependencies, and MCP tools"},
	{ID: "resume", Icon: "↗", Title: "Resume nginx migration", Desc: "Updated 3 days ago · 82% · 2 to review", Meta: "82%"},
}

// Prefill texts written into the prompt when an action is activated (spec
// §9.1).
const (
	PrefillMigrate = "Migrate the current project to Kunpeng ARM64"
	PrefillScan    = "Scan the current workspace for Kunpeng compatibility"
	PrefillResume  = "Resume the nginx migration task"
)

// ActionsState carries the focus, selection, hover and transient states the
// list needs to render.
type ActionsState struct {
	Focused   bool
	Selected  int
	Hover     int    // -1 when no hover
	Spinner   string // spinner frame shown on the resume item while restoring; "" to hide
	Collapsed bool   // tight single-column: resume item collapses to one row
}

// RenderActions renders the suggestion list. Items are two rows each (track,
// icon, title, meta on the first; description on the second) with one gap row
// between items (spec §9.2). The selection highlight (left ┃ + surface bg +
// bold title) is only shown while the list has keyboard focus — the accent
// quota in §5.3 allows exactly one purple at a time.
func RenderActions(t theme.Theme, w int, s ActionsState) *Block {
	heights := []int{2, 2, 2}
	total := 8
	if s.Collapsed {
		heights[2] = 1
		total = 7
	}
	blk := NewBlock(t, w, total)
	y := 0
	for i, a := range Actions {
		st := theme.ActionIdle
		if s.Hover == i {
			st = theme.ActionHover
		}
		if s.Focused && s.Selected == i {
			st = theme.ActionSelected
		}
		icon := a.Icon
		if i == 2 && s.Spinner != "" {
			icon = s.Spinner
		}
		rows := renderActionRows(t, w, a, st, icon, heights[i] == 1)
		for j, ln := range rows {
			blk.Set(t, y+j, ln)
		}
		y += heights[i] + 1
	}
	return blk
}

// renderActionRows renders the 1-2 lines of one action item. Each line is a
// sequence of segments all carrying the row background, so the row highlight
// spans the whole action column width (spec §9.2).
func renderActionRows(t theme.Theme, w int, a Action, st theme.ActionState, icon string, collapsed bool) []string {
	as := t.Action(st)
	bg := as.Bg
	if bg == "" {
		bg = t.P.BgBase
	}
	trackCh := "│"
	if st == theme.ActionSelected || st == theme.ActionPressed {
		trackCh = "┃"
	}
	track := t.Style(as.Track, bg).Render(trackCh)
	spacer := func(n int) string { return t.Style("", bg).Render(strings.Repeat(" ", n)) }

	// Row 1: track + " " + icon + "  " + title  (title at col 5) + meta right-aligned
	iconSeg := t.Style(as.Icon, bg).Render(" " + icon + "  ")
	titleSeg := t.Style(as.Title, bg)
	if as.TitleBold {
		titleSeg = titleSeg.Bold(true)
	}
	title := titleSeg.Render(a.Title)

	left := track + iconSeg + title
	row1 := left
	if a.Meta != "" {
		metaSeg := t.Style(t.P.TextSecondary, bg).Render(a.Meta)
		fill := w - lipgloss.Width(left) - lipgloss.Width(metaSeg) - 1
		if fill > 0 {
			row1 = left + spacer(fill) + metaSeg
		} else {
			row1 = left + spacer(w-lipgloss.Width(left))
		}
	} else {
		row1 = left + spacer(w-lipgloss.Width(left))
	}

	if collapsed {
		return []string{row1}
	}

	// Row 2: track + 4 spaces + description
	desc := t.Style(as.Desc, bg).Render(a.Desc)
	row2 := track + spacer(4) + desc + spacer(w-5-lipgloss.Width(desc))
	return []string{row1, row2}
}
