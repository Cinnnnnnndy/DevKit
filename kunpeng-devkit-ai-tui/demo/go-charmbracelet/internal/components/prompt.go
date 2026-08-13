package components

import "devkitai/internal/theme"

// PromptState carries everything the prompt box needs to render (spec §8).
type PromptState struct {
	Focused     bool
	Err         bool
	Spinner     string // spinner frame shown left of the input while submitting
	Label       string // "Ask DevKit AI", "Starting task", "✓ Task ready"
	InputView   string // textinput.View(): value/placeholder + cursor
	HintText    string // "" hides the hint; e.g. "enter ↵"
	HintVisible bool
	EmptyPulse  bool   // 120ms border emphasis on empty Enter
	ErrorText   string // one-line error below the box; "" hides
}

// Prompt renders the 3-row rounded input box (4 rows with an error line).
// Focus shows the single purple border + pink label (spec §5.3); on error the
// border and label turn danger. The interior is a surface panel (spec §5.1).
func Prompt(t theme.Theme, w int, s PromptState) *Block {
	var labelColor string
	switch {
	case s.Err:
		labelColor = t.P.StateDanger
	case s.Focused:
		labelColor = t.P.AccentPink
	default:
		labelColor = t.P.TextMuted
	}
	label := t.Style(labelColor, "").Render(s.Label)

	var borderFg string
	switch {
	case s.Err:
		borderFg = t.P.StateDanger
	case s.Focused:
		borderFg = t.P.AccentPurple
	default:
		borderFg = t.P.BorderSubtle
	}

	bottomMid := ""
	if s.HintText != "" && s.HintVisible {
		bottomMid = t.Style(t.P.TextMuted, "").Render(s.HintText)
	}

	content := []string{"  " + s.InputView}
	if s.Spinner != "" {
		content = []string{"  " + s.Spinner + " " + s.InputView}
	}
	box := BoxBold(t, w, 3, borderFg, t.P.BgSurface, label, bottomMid, content, s.EmptyPulse)

	if s.ErrorText == "" {
		return box
	}
	blk := NewBlock(t, w, 4)
	for i, ln := range box.Lines {
		blk.Set(t, i, ln)
	}
	blk.Set(t, 3, t.Style(t.P.StateDanger, "").Render(s.ErrorText))
	return blk
}
