package app

import (
	"os"

	"charm.land/bubbles/v2/spinner"
	"charm.land/bubbles/v2/textinput"

	"devkitai/internal/theme"
)

// FocusArea tracks which region holds keyboard focus (spec §14: focus and
// phase must stay separate enums).
type FocusArea int

const (
	FocusPrompt FocusArea = iota
	FocusActions
)

// Phase tracks the business phase (spec §17.3).
type Phase int

const (
	PhaseBoot Phase = iota
	PhaseReady
	PhaseSubmitting
	PhaseRestoring
	PhaseFeedback
	PhaseError
)

// Model is the Bubble Tea model for the Launch screen.
type Model struct {
	width, height int

	focus    FocusArea
	phase    Phase
	selected int
	hover    int // -1 when no mouse hover

	input   textinput.Model
	spinner spinner.Model

	reveal         int // entrance stage 0..5 (spec §13.1)
	feedback       string
	feedbackDimmed bool
	errMsg         string
	emptyPulse     bool
	restored       bool // a resume session finished → "✓ Session restored" status

	noAnimation    bool
	darkBackground bool

	th theme.Theme
}

// New builds the Launch model. NO_COLOR is honored from the environment
// (spec §5.4).
func New(noAnimation bool) Model {
	t := theme.Theme{P: theme.Default, NoColor: os.Getenv("NO_COLOR") != ""}

	ti := textinput.New()
	ti.Placeholder = "Describe a migration, build, diagnosis, or optimization task…"
	ti.Prompt = ""
	ti.CharLimit = 500
	ti.SetWidth(60)
	st := ti.Styles()
	st.Focused.Text = t.SurfaceText(t.P.TextPrimary)
	st.Focused.Placeholder = t.SurfaceText(t.P.TextMuted)
	st.Blurred.Text = t.SurfaceText(t.P.TextPrimary)
	st.Blurred.Placeholder = t.SurfaceText(t.P.TextMuted)
	ti.SetStyles(st)
	ti.Focus() // prompt auto-focuses on launch (spec §18.3)

	sp := spinner.New()
	sp.Spinner = spinner.Dot
	sp.Style = t.Style(t.P.TextSecondary, t.P.BgBase)

	reveal := 0
	phase := PhaseBoot
	if noAnimation {
		// Reduced motion: everything appears on the first frame (spec §13.4).
		reveal = 5
		phase = PhaseReady
	}

	return Model{
		focus:          FocusPrompt,
		phase:          phase,
		selected:       0,
		hover:          -1,
		input:          ti,
		spinner:        sp,
		reveal:         reveal,
		noAnimation:    noAnimation,
		darkBackground: true,
		th:             t,
	}
}
