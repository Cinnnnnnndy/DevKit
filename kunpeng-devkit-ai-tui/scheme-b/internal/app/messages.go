package app

// Confirmed Charm v2 API surface (verified against module source in
// GOMODCACHE, 2026-08): see cmd/spike notes. The essentials used here:
//
//   - Model: Init() tea.Cmd; Update(tea.Msg) (tea.Model, tea.Cmd); View() tea.View
//   - tea.View: Content string, AltScreen bool, MouseMode tea.MouseMode,
//     DisableBracketedPasteMode bool (default: bracketed paste ON), WindowTitle string
//   - Keys: tea.KeyPressMsg (alias of Key). msg.String() → "enter","down","up",
//     "tab","esc","ctrl+u","ctrl+c","ctrl+q". Key struct: Text string, Mod KeyMod,
//     Code rune. Constants: tea.KeyEnter/KeyTab/KeyEscape/KeyUp/KeyDown/KeyBackspace.
//   - Mouse: MouseMsg interface with concrete MouseClickMsg / MouseMotionMsg /
//     MouseReleaseMsg / MouseWheelMsg, each .Mouse() → Mouse{X, Y int, Button}.
//     MouseLeft is the button const.
//   - Window: tea.WindowSizeMsg{Width, Height} sent on start and every resize.
//   - Commands: tea.Batch, tea.Sequence, tea.Tick(d, fn), tea.Quit() Msg,
//     tea.RequestWindowSize() Msg.
//   - Program: tea.NewProgram(model, tea.WithWindowSize(w,h),
//     tea.WithColorProfile(profile), tea.WithInput, tea.WithOutput).
//   - Bubbles textinput: textinput.New(); fields Placeholder/CharLimit/Width;
//     methods SetWidth/SetValue/Value()/SetCursor/CursorEnd()/Position()/Focus()
//     tea.Cmd/Blur()/Focused(); Styles()/SetStyles(Styles{Focused StyleState
//     {Text,Placeholder,Suggestion,Prompt}, Blurred StyleState, Cursor}).
//   - Bubbles spinner: spinner.New(); spinner.Dot (braille @100ms) & spinner.Line
//     (| / - \); (m).Update(msg) (Model, Cmd); (m).View(); (m).Tick() tea.Msg —
//     start by returning the method value m.spinner.Tick as the command; it
//     self-perpetuates through spinner.TickMsg until no longer forwarded.
//   - Lip Gloss v2: lipgloss.NewStyle(), .Foreground/.Background(lipgloss.Color("#hex")),
//     .Border(lipgloss.RoundedBorder()), .Padding, .Width/.Height, .Bold, .Render();
//     lipgloss.Color("") → no color (NO_COLOR). Nested backgrounds survive: an
//     inner surface background overrides the outer base wrapper (verified by
//     experiment). lipgloss.Width(str) measures visible width incl. ANSI.
//   - colorprofile.TrueColor / ANSI256 / ANSI / ASCII for tests.

// RevealStageMsg advances the entrance reveal (spec §13.1). Stage 1..5 map to
// Brand / Prompt / Actions / Environment / Keyhelp appearing.
type RevealStageMsg struct{ Stage int }

// PulseDoneMsg ends the 120ms empty-Enter border emphasis (spec §8.3).
type PulseDoneMsg struct{}

// SubmitResultMsg reports the simulated task-submit outcome (spec §14).
type SubmitResultMsg struct {
	OK  bool
	Err string
}

// RestoreResultMsg reports the simulated resume outcome (spec §14).
type RestoreResultMsg struct {
	OK  bool
	Err string
}

// FeedbackDimMsg dims the feedback line 2.5s after it appears (spec §14).
type FeedbackDimMsg struct{}
