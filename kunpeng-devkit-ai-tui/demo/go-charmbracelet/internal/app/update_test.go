package app

import (
	"testing"

	"charm.land/bubbletea/v2"

	"devkitai/internal/components"
	"devkitai/internal/layout"
)

// kp builds a key press message by name for tests.
func kp(s string) tea.KeyPressMsg {
	switch s {
	case "enter":
		return tea.KeyPressMsg{Code: tea.KeyEnter}
	case "down":
		return tea.KeyPressMsg{Code: tea.KeyDown}
	case "up":
		return tea.KeyPressMsg{Code: tea.KeyUp}
	case "tab":
		return tea.KeyPressMsg{Code: tea.KeyTab}
	case "esc":
		return tea.KeyPressMsg{Code: tea.KeyEscape}
	case "ctrl+u":
		return tea.KeyPressMsg{Code: 'u', Mod: tea.ModCtrl}
	case "ctrl+c":
		return tea.KeyPressMsg{Code: 'c', Mod: tea.ModCtrl}
	case "ctrl+q":
		return tea.KeyPressMsg{Code: 'q', Mod: tea.ModCtrl}
	default:
		return tea.KeyPressMsg{Text: s}
	}
}

// newTestModel returns a launched model at the canonical viewport.
func newTestModel() Model {
	m := New(true) // no animation → PhaseReady, reveal 5
	m.width, m.height = 156, 48
	return m
}

// apply feeds a message through Update and returns the resulting model.
func apply(m Model, msg tea.Msg) Model {
	got, _ := m.Update(msg)
	return got.(Model)
}

func TestLaunchState(t *testing.T) {
	m := newTestModel()
	if m.focus != FocusPrompt {
		t.Errorf("focus = %v, want FocusPrompt", m.focus)
	}
	if m.phase != PhaseReady {
		t.Errorf("phase = %v, want PhaseReady", m.phase)
	}
	if !m.input.Focused() {
		t.Error("input should start focused (spec §18.3)")
	}
}

func TestDownFromPromptEntersActions(t *testing.T) {
	m := apply(newTestModel(), kp("down"))
	if m.focus != FocusActions || m.selected != 0 {
		t.Errorf("focus=%v selected=%d, want FocusActions/0", m.focus, m.selected)
	}
}

func TestActionsClampNavigation(t *testing.T) {
	m := newTestModel()
	for i := 0; i < 5; i++ { // down x5 should clamp at the last item
		m = apply(m, kp("down"))
	}
	if m.selected != 2 {
		t.Errorf("selected = %d, want 2 (clamped)", m.selected)
	}
	// Up returns to previous
	m = apply(m, kp("up"))
	if m.selected != 1 {
		t.Errorf("after up selected = %d, want 1", m.selected)
	}
	// Up from the top returns to prompt
	m = apply(m, kp("up"))
	m = apply(m, kp("up"))
	if m.focus != FocusPrompt {
		t.Errorf("up from top should return to prompt, focus=%v", m.focus)
	}
}

func TestTabCycles(t *testing.T) {
	m := apply(newTestModel(), kp("tab"))
	if m.focus != FocusActions {
		t.Fatalf("tab should enter actions, focus=%v", m.focus)
	}
	m = apply(m, kp("tab"))
	if m.focus != FocusPrompt {
		t.Errorf("tab should return to prompt, focus=%v", m.focus)
	}
}

func TestTyping(t *testing.T) {
	m := apply(newTestModel(), kp("hello world"))
	if got := m.input.Value(); got != "hello world" {
		t.Errorf("value = %q, want %q", got, "hello world")
	}
}

func TestEmptyEnterPulsesNoError(t *testing.T) {
	got, cmd := newTestModel().Update(kp("enter"))
	m := got.(Model)
	if !m.emptyPulse {
		t.Error("empty enter should set the 120ms emphasis pulse (spec §8.3)")
	}
	if cmd == nil {
		t.Error("empty enter should schedule the pulse-done tick")
	}
	// The pulse clears on PulseDoneMsg.
	m = apply(m, PulseDoneMsg{})
	if m.emptyPulse {
		t.Error("pulse should clear on PulseDoneMsg")
	}
}

func TestSubmitFlow(t *testing.T) {
	m := apply(newTestModel(), kp("migrate nginx"))
	got, cmd := m.Update(kp("enter"))
	m = got.(Model)
	if m.phase != PhaseSubmitting {
		t.Fatalf("phase = %v, want PhaseSubmitting", m.phase)
	}
	if cmd == nil {
		t.Fatal("submit should schedule the 450ms result tick")
	}
	if m.input.Value() == "" {
		t.Error("input value should be retained during submit")
	}
	// Complete the submit.
	m = apply(m, SubmitResultMsg{OK: true})
	if m.phase != PhaseFeedback {
		t.Errorf("phase = %v, want PhaseFeedback", m.phase)
	}
	if m.feedback == "" {
		t.Error("feedback text should be set")
	}
	// Feedback dims but does not dismiss (spec §14).
	m = apply(m, FeedbackDimMsg{})
	if !m.feedbackDimmed {
		t.Error("feedback should dim after 2.5s")
	}
	if m.feedback == "" {
		t.Error("feedback should not auto-dismiss")
	}
}

func TestEscSemantics(t *testing.T) {
	// With content: Esc clears.
	m := apply(newTestModel(), kp("abc"))
	m = apply(m, kp("esc"))
	if m.input.Value() != "" {
		t.Errorf("esc should clear value, got %q", m.input.Value())
	}
	// With empty content: Esc focuses the first action.
	m = apply(m, kp("esc"))
	if m.focus != FocusActions || m.selected != 0 {
		t.Errorf("esc on empty should focus actions, focus=%v selected=%d", m.focus, m.selected)
	}
}

func TestCtrlUClears(t *testing.T) {
	m := apply(newTestModel(), kp("delete me"))
	m = apply(m, kp("ctrl+u"))
	if m.input.Value() != "" {
		t.Errorf("ctrl+u should clear, got %q", m.input.Value())
	}
}

func TestQQuitsOnlyWithoutInputFocus(t *testing.T) {
	// While typing in the prompt, "q" is a character, not a quit.
	m := apply(newTestModel(), kp("q"))
	if m.input.Value() != "q" {
		t.Errorf("q should type into the prompt, value=%q", m.input.Value())
	}
	// With actions focused, q quits.
	m = apply(m, kp("down"))
	got, cmd := m.Update(kp("q"))
	if cmd == nil {
		t.Fatal("q with actions focus should return a quit command (spec §11)")
	}
	if got.(Model).input.Value() != "q" {
		t.Error("q should not type into the input when actions focused")
	}
}

func TestCtrlQQuitsAlways(t *testing.T) {
	got, cmd := newTestModel().Update(kp("ctrl+q"))
	if cmd == nil {
		t.Fatal("ctrl+q should always quit")
	}
	_ = got
}

func TestCharLimit(t *testing.T) {
	m := newTestModel()
	long := ""
	for i := 0; i < 600; i++ {
		long += "a"
	}
	m = apply(m, kp(long))
	if got := len([]rune(m.input.Value())); got != 500 {
		t.Errorf("value length = %d, want 500 (CharLimit, spec §8.3)", got)
	}
}

func TestMigratePrefillsPrompt(t *testing.T) {
	m := newTestModel()
	m = apply(m, kp("down")) // focus actions, selected migrate
	m = apply(m, kp("enter"))
	if m.focus != FocusPrompt {
		t.Errorf("focus = %v, want FocusPrompt after prefill (spec §9.4)", m.focus)
	}
	if m.input.Value() != components.PrefillMigrate {
		t.Errorf("value = %q, want %q", m.input.Value(), components.PrefillMigrate)
	}
	if m.phase != PhaseReady {
		t.Errorf("prefill must not auto-submit, phase=%v", m.phase)
	}
}

func TestScanPrefillsPrompt(t *testing.T) {
	m := newTestModel()
	m = apply(m, kp("down"))
	m = apply(m, kp("down")) // selected scan
	m = apply(m, kp("enter"))
	if m.input.Value() != components.PrefillScan {
		t.Errorf("value = %q, want %q", m.input.Value(), components.PrefillScan)
	}
}

func TestResumeFlow(t *testing.T) {
	m := newTestModel()
	for i := 0; i < 3; i++ {
		m = apply(m, kp("down"))
	}
	got, cmd := m.Update(kp("enter"))
	m = got.(Model)
	if m.phase != PhaseRestoring {
		t.Fatalf("phase = %v, want PhaseRestoring", m.phase)
	}
	if cmd == nil {
		t.Fatal("resume should start the spinner")
	}
	m = apply(m, RestoreResultMsg{OK: true})
	if m.phase != PhaseFeedback || !m.restored {
		t.Errorf("restore should reach feedback, phase=%v restored=%v", m.phase, m.restored)
	}
}

func TestResizePreservesState(t *testing.T) {
	m := newTestModel()
	m = apply(m, kp("keep me"))
	m = apply(m, kp("down"))
	m = apply(m, kp("down")) // selected scan
	m = apply(m, tea.WindowSizeMsg{Width: 100, Height: 32})
	if m.input.Value() != "keep me" {
		t.Errorf("input lost after resize: %q", m.input.Value())
	}
	if m.focus != FocusActions || m.selected != 1 {
		t.Errorf("selection lost after resize: focus=%v selected=%d", m.focus, m.selected)
	}
}

func TestMouseHoverDoesNotStealFocus(t *testing.T) {
	m := newTestModel() // prompt focused
	met := layout.Compute(156, 48)
	y := met.ActionRects[1].Y
	got, _ := m.Update(tea.MouseMotionMsg{X: met.ActionRects[1].X + 5, Y: y})
	m = got.(Model)
	if m.hover != 1 {
		t.Errorf("hover = %d, want 1", m.hover)
	}
	if m.focus != FocusPrompt {
		t.Errorf("hover must not steal focus, focus=%v", m.focus)
	}
}

func TestMouseClickActivatesAction(t *testing.T) {
	m := newTestModel()
	met := layout.Compute(156, 48)
	// Click the scan item.
	got, _ := m.Update(tea.MouseClickMsg{X: met.ActionRects[1].X + 5, Y: met.ActionRects[1].Y + 1, Button: tea.MouseLeft})
	m = got.(Model)
	if m.input.Value() != components.PrefillScan {
		t.Errorf("click should prefill scan, value=%q", m.input.Value())
	}
	if m.focus != FocusPrompt {
		t.Errorf("click should return focus to prompt, focus=%v", m.focus)
	}
}
