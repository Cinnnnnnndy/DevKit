package components

import (
	"strings"

	"charm.land/lipgloss/v2"

	"devkitai/internal/theme"
)

// EnvItem is one status segment of the summary line (spec §10).
type EnvItem struct {
	Kind   theme.StatusKind
	Symbol string // semantic symbol that survives NO_COLOR (§5.4)
	Text   string
}

// EnvState describes the environment summary row. When Spinner is non-empty
// it replaces the item list with a spinner + transient text (spec §10.2);
// otherwise the items are shown with separators, trimmed from the right when
// the width runs out (spec §4.3: Runtime first, then MCP, then ARM64).
type EnvState struct {
	Spinner     string
	SpinnerText string
	Items       []EnvItem
}

// DefaultEnvItems is the canonical status line (spec §10.1).
var DefaultEnvItems = []EnvItem{
	{Kind: theme.StatusRuntime, Symbol: "●", Text: "Runtime ready"},
	{Kind: theme.StatusMCP, Symbol: "▲", Text: "2/4 MCP tools"},
	{Kind: theme.StatusARM64, Symbol: "", Text: "ARM64 toolchain"},
}

// Environment renders the one-row status summary.
func Environment(t theme.Theme, w int, s EnvState) string {
	if s.Spinner != "" {
		spinner := t.Style(t.P.TextSecondary, "").Render(s.Spinner)
		text := t.Style(t.P.TextSecondary, "").Render(" " + s.SpinnerText)
		return spinner + text
	}
	segs := make([]string, 0, len(s.Items))
	for _, it := range s.Items {
		var sym string
		if it.Symbol != "" {
			sym = t.Style(t.Status(it.Kind), "").Render(it.Symbol)
		}
		var txt string
		if it.Kind == theme.StatusARM64 {
			txt = t.Style(t.P.AccentCyan, "").Render(it.Text)
		} else {
			txt = t.Style(t.P.TextSecondary, "").Render(it.Text)
		}
		segs = append(segs, sym+" "+txt)
	}
	sep := t.Style(t.P.TextDisabled, "").Render("  ·  ")
	return assembleWithSep(segs, sep, w)
}

// assembleWithSep joins segments left-to-right with the separator, dropping
// trailing segments once the running width would exceed the budget.
func assembleWithSep(segs []string, sep string, w int) string {
	var b strings.Builder
	width := 0
	for i, s := range segs {
		sw := lipgloss.Width(s)
		if i > 0 {
			sws := lipgloss.Width(sep)
			if width+sws+sw > w {
				break
			}
			b.WriteString(sep)
			width += sws
		}
		b.WriteString(s)
		width += sw
	}
	return b.String()
}
