package components

import (
	"strings"

	"devkitai/internal/theme"
)

// KeyHelp renders the one-line shortcut bar (spec §11): keys in secondary,
// descriptions in muted, two-space gaps, no capsules. enterLabel switches
// with focus context ("submit" vs "select"). compact drops the navigation
// group first (spec §4.3: keep enter and ctrl+q).
func KeyHelp(t theme.Theme, w int, enterLabel string, compact bool) string {
	groups := []string{
		"↑↓ navigate",
		"enter " + enterLabel,
		"ctrl+q quit",
	}
	if compact {
		groups = groups[1:]
	}
	segs := make([]string, 0, len(groups))
	for _, g := range groups {
		key, desc, _ := strings.Cut(g, " ")
		segs = append(segs, t.Style(t.P.TextSecondary, "").Render(key)+" "+t.Style(t.P.TextMuted, "").Render(desc))
	}
	return strings.Join(segs, "  ")
}
