package app

import (
	"fmt"

	"charm.land/bubbletea/v2"
	"charm.land/lipgloss/v2"
	"github.com/mattn/go-runewidth"

	"devkitai/internal/components"
	"devkitai/internal/layout"
	"devkitai/internal/theme"
)

// View renders the Launch screen. AltScreen, mouse motion and bracketed paste
// are declared declaratively on the tea.View (v2 style).
func (m Model) View() tea.View {
	v := tea.NewView(m.render())
	v.AltScreen = true
	v.MouseMode = tea.MouseModeAllMotion
	v.WindowTitle = "Kunpeng DevKit AI"
	return v
}

// render is the pure, deterministic frame builder (§17.4): it never performs
// I/O or runs commands.
func (m Model) render() string {
	t := m.th
	met := layout.Compute(m.width, m.height)
	if met.Tier == layout.TierTooSmall {
		return renderTooSmall(t, m.width, m.height)
	}

	rightW := met.RightW
	gap := 1
	if met.Tight {
		gap = 0
	}

	prompt := m.promptBlock(t, rightW)
	feedback := m.feedbackBlock(t, rightW)
	label := m.actionsLabelBlock(t, rightW)
	actions := m.actionsBlock(t, rightW, met.Tight)
	status := m.envBlock(t, rightW)
	help := m.helpBlock(t, rightW, met.Tight)

	// Entrance reveal (§13.1): unrevealed regions render blank blocks of the
	// same geometry, so nothing jumps during the 420ms stagger.
	prompt = revealIf(t, m.reveal >= 2, prompt)
	label = revealIf(t, m.reveal >= 3, label)
	actions = revealIf(t, m.reveal >= 3, actions)
	status = revealIf(t, m.reveal >= 4, status)
	help = revealIf(t, m.reveal >= 5, help)

	var content *components.Block
	if met.Tier == layout.TierDual {
		left := components.FullBrand(t)
		left = revealIf(t, m.reveal >= 1, left)
		right := components.JoinV(t, gap, prompt, feedback, label, actions, status, help)
		content = components.JoinH(t, met.Gap, left, right)
	} else {
		brand := m.compactBrandBlock(t, rightW)
		brand = revealIf(t, m.reveal >= 1, brand)
		content = components.JoinV(t, gap, brand, prompt, feedback, label, actions, status, help)
	}
	return components.ComposeScreen(t, m.width, m.height, met.CX, met.CY, content)
}

// revealIf blanks a block until its entrance stage has fired.
func revealIf(t theme.Theme, visible bool, blk *components.Block) *components.Block {
	if visible {
		return blk
	}
	return components.NewBlock(t, blk.Width, blk.Height())
}

func (m Model) promptBlock(t theme.Theme, w int) *components.Block {
	s := components.PromptState{
		Focused:     m.focus == FocusPrompt,
		Err:         m.phase == PhaseError,
		Label:       "Ask DevKit AI",
		InputView:   m.input.View(),
		HintText:    "enter ↵",
		HintVisible: true,
		EmptyPulse:  m.emptyPulse,
		ErrorText:   m.errMsg,
	}
	switch m.phase {
	case PhaseSubmitting:
		s.Label = "Starting task"
		s.Spinner = m.spinner.View()
		s.HintText = ""
	case PhaseFeedback:
		s.Label = "✓ Task ready"
		s.HintText = ""
	}
	// Hide the submit hint once the input reaches the right edge (§8.1).
	if w > 0 && runewidth.StringWidth(m.input.Value()) >= w-6 {
		s.HintVisible = false
	}
	return components.Prompt(t, w, s)
}

func (m Model) feedbackBlock(t theme.Theme, w int) *components.Block {
	blk := components.NewBlock(t, w, 1)
	if m.phase == PhaseFeedback && m.feedback != "" {
		style := t.Style(t.P.StateSuccess, t.P.BgBase)
		if m.feedbackDimmed {
			style = t.Style(t.P.TextMuted, t.P.BgBase)
		}
		blk.Set(t, 0, style.Render(m.feedback))
	}
	return blk
}

func (m Model) actionsLabelBlock(t theme.Theme, w int) *components.Block {
	blk := components.NewBlock(t, w, 1)
	blk.Set(t, 0, t.Muted().Render("Start with an action"))
	return blk
}

func (m Model) actionsBlock(t theme.Theme, w int, collapsed bool) *components.Block {
	spin := ""
	if m.phase == PhaseRestoring && m.selected == 2 {
		spin = m.spinner.View()
	}
	return components.RenderActions(t, w, components.ActionsState{
		Focused:   m.focus == FocusActions,
		Selected:  m.selected,
		Hover:     m.hover,
		Spinner:   spin,
		Collapsed: collapsed,
	})
}

func (m Model) envBlock(t theme.Theme, w int) *components.Block {
	blk := components.NewBlock(t, w, 1)
	var line string
	switch m.phase {
	case PhaseSubmitting:
		line = components.Environment(t, w, components.EnvState{Spinner: m.spinner.View(), SpinnerText: "Preparing task…"})
	case PhaseRestoring:
		line = components.Environment(t, w, components.EnvState{Spinner: m.spinner.View(), SpinnerText: "Restoring session…"})
	case PhaseFeedback:
		if m.restored {
			line = components.Environment(t, w, components.EnvState{Items: []components.EnvItem{
				{Kind: theme.StatusRuntime, Symbol: "✓", Text: "Session restored"},
			}})
		} else {
			line = components.Environment(t, w, components.EnvState{Items: components.DefaultEnvItems})
		}
	default:
		line = components.Environment(t, w, components.EnvState{Items: components.DefaultEnvItems})
	}
	blk.Set(t, 0, line)
	return blk
}

func (m Model) helpBlock(t theme.Theme, w int, compact bool) *components.Block {
	enterLabel := "submit"
	if m.focus == FocusActions {
		enterLabel = "select"
	}
	blk := components.NewBlock(t, w, 1)
	blk.Set(t, 0, components.KeyHelp(t, w, enterLabel, compact))
	return blk
}

func (m Model) compactBrandBlock(t theme.Theme, w int) *components.Block {
	blk := components.NewBlock(t, w, 1)
	blk.Set(t, 0, compactBrandLine(t, w))
	return blk
}

// compactBrandLine renders the one-line brand with priority hiding when the
// width runs out (spec §7.2): READY → separator → KUNPENG → minimum.
func compactBrandLine(t theme.Theme, w int) string {
	mark := components.CompactMark(t)
	wordFull := t.Style(t.P.TextPrimary, t.P.BgBase).Bold(true).Render("KUNPENG DEVKIT AI")
	wordShort := t.Style(t.P.TextPrimary, t.P.BgBase).Bold(true).Render("DEVKIT AI")
	dot := t.Style(t.P.StateSuccess, t.P.BgBase).Render("●")
	arm := t.Style(t.P.TextSecondary, t.P.BgBase).Render(" ARM64")
	ready := t.Style(t.P.TextSecondary, t.P.BgBase).Render(" READY")
	sep := t.Style(t.P.TextDisabled, t.P.BgBase).Render("  ·  ")
	gap2 := t.Style(t.P.BgBase, t.P.BgBase).Render("  ")

	candidates := []string{
		mark + gap2 + wordFull + sep + dot + arm + ready,
		mark + gap2 + wordFull + sep + dot + arm,
		mark + gap2 + wordFull + gap2 + dot + arm,
		mark + gap2 + wordShort + gap2 + dot + arm,
		mark + gap2 + wordShort,
	}
	for _, c := range candidates {
		if lipgloss.Width(c) <= w {
			return c
		}
	}
	return candidates[len(candidates)-1]
}

// renderTooSmall draws the size-required page (spec §4.4). No animation, key
// numbers never truncated; it returns to Launch automatically on resize.
func renderTooSmall(t theme.Theme, w, h int) string {
	boxW := 40
	if w-2 < boxW {
		boxW = w - 2
	}
	if boxW < 20 {
		boxW = 20
	}
	content := []string{
		"  Terminal is too small",
		fmt.Sprintf("  Current %d×%d · Required 72×24", w, h),
		"  Resize the window to continue.",
	}
	title := t.Style(t.P.TextPrimary, t.P.BgBase).Bold(true).Render("Kunpeng DevKit AI")
	box := components.Box(t, boxW, 5, t.P.BorderStrong, t.P.BgSurface, title, "", content)
	cx := (w - boxW) / 2
	cy := (h - 5) / 2
	if cx < 0 {
		cx = 0
	}
	if cy < 0 {
		cy = 0
	}
	return components.ComposeScreen(t, w, h, cx, cy, box)
}
