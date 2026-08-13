package theme

import (
	"image/color"

	"charm.land/lipgloss/v2"
)

// Theme carries the palette plus degradation flags. All style builders are
// pure functions of the theme; rendering stays deterministic (spec §17.4).
type Theme struct {
	P       Palette
	NoColor bool
}

// Color maps a hex token to a lipgloss color. In NO_COLOR mode (or for an
// empty token) it returns the no-color sentinel so no SGR is emitted (spec
// §5.4).
func (t Theme) Color(hex string) color.Color {
	if t.NoColor || hex == "" {
		return lipgloss.Color("")
	}
	return lipgloss.Color(hex)
}

// Style builds a base style from optional fg/bg hex tokens. Every segment
// rendered on screen must carry an explicit background so segment boundaries
// never leak the terminal's default color; when bg is empty it defaults to
// the canonical base background (spec §12.1). In NO_COLOR mode no color SGR
// is emitted at all.
func (t Theme) Style(fg, bg string) lipgloss.Style {
	s := lipgloss.NewStyle()
	if t.NoColor {
		return s
	}
	if fg != "" {
		s = s.Foreground(t.Color(fg))
	}
	if bg == "" {
		bg = t.P.BgBase
	}
	return s.Background(t.Color(bg))
}

// Text helpers: primary / secondary / muted / disabled foreground styles.
func (t Theme) Primary() lipgloss.Style   { return t.Style(t.P.TextPrimary, "") }
func (t Theme) Secondary() lipgloss.Style { return t.Style(t.P.TextSecondary, "") }
func (t Theme) Muted() lipgloss.Style     { return t.Style(t.P.TextMuted, "") }
func (t Theme) Disabled() lipgloss.Style  { return t.Style(t.P.TextDisabled, "") }

// Base fills a region with the canonical background (spec §12.1). Every cell
// of the final screen — including padding and blank rows — must carry this.
func (t Theme) Base() lipgloss.Style { return t.Style("", t.P.BgBase) }

// Surface is a local raised background (prompt box, selected action, badge).
func (t Theme) Surface() lipgloss.Style { return t.Style("", t.P.BgSurface) }

// SurfaceText styles text that sits inside a surface panel, so the cells keep
// the surface background (no base "holes" under the raised area).
func (t Theme) SurfaceText(fg string) lipgloss.Style { return t.Style(fg, t.P.BgSurface) }

// PromptBorder returns the border style for the task input box. Focused uses
// the single purple accent (spec §5.3); error uses danger; idle uses subtle.
// In NO_COLOR the focused border becomes bold so focus keeps two signals
// (border + bold, spec §16 / §5.4).
func (t Theme) PromptBorder(focused, err bool) lipgloss.Style {
	s := t.Base()
	s = s.BorderForeground(t.Color(t.P.BorderSubtle))
	switch {
	case err:
		s = s.BorderForeground(t.Color(t.P.StateDanger))
	case focused:
		if t.NoColor {
			s = s.Bold(true)
		}
		s = s.BorderForeground(t.Color(t.P.AccentPurple))
	}
	return s
}

// PromptLabel styles the "Ask DevKit AI" label: muted idle, pink on focus.
func (t Theme) PromptLabel(focused, err bool) lipgloss.Style {
	switch {
	case err:
		return t.Style(t.P.StateDanger, "")
	case focused:
		return t.Style(t.P.AccentPink, "")
	default:
		return t.Muted()
	}
}

// ActionRow returns the style for a suggestion action row region (spec §9.2):
// the track color, icon color, title color and background are derived from
// the row state. Titles render bold for selected/pressed.
type ActionStyle struct {
	Track     string
	Icon      string
	Title     string
	Desc      string
	Bg        string
	TitleBold bool
}

func (t Theme) Action(state ActionState) ActionStyle {
	p := t.P
	switch state {
	case ActionSelected, ActionPressed:
		bg := p.BgSurface
		if state == ActionPressed {
			bg = p.BgSurfaceActive
		}
		return ActionStyle{
			Track:     p.AccentPurple,
			Icon:      p.AccentPink,
			Title:     p.TextPrimary,
			Desc:      p.TextSecondary,
			Bg:        bg,
			TitleBold: true,
		}
	case ActionHover:
		return ActionStyle{
			Track: p.TextSecondary,
			Icon:  p.TextSecondary,
			Title: p.TextPrimary,
			Desc:  p.TextSecondary,
			Bg:    p.BgSurfaceHover,
		}
	case ActionDisabled:
		return ActionStyle{Track: p.TextDisabled, Icon: p.TextDisabled, Title: p.TextDisabled, Desc: p.TextDisabled}
	default: // idle
		return ActionStyle{Track: "", Icon: p.TextMuted, Title: p.TextSecondary, Desc: p.TextMuted}
	}
}

// Status returns the semantic color for an environment status item. Runtime
// is success, MCP partial-warning, ARM64 is informational cyan (spec §10.1).
func (t Theme) Status(kind StatusKind) string {
	p := t.P
	switch kind {
	case StatusRuntime:
		return p.StateSuccess
	case StatusMCP:
		return p.StateWarning
	case StatusARM64:
		return p.AccentCyan
	}
	return p.TextMuted
}
