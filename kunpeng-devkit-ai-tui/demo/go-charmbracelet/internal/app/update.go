package app

import (
	"time"

	"charm.land/bubbletea/v2"

	"devkitai/internal/components"
	"devkitai/internal/layout"
)

// revealTimings are the delays between entrance stages (spec §13.1): stages
// land at 60 / 140 / 240 / 340 / 420 ms. After stage 5 no tick remains, so
// idle never redraws (spec §17.5).
var revealTimings = []time.Duration{
	60 * time.Millisecond,
	80 * time.Millisecond,
	100 * time.Millisecond,
	100 * time.Millisecond,
	80 * time.Millisecond,
}

func revealCmd(stage int) tea.Cmd {
	if stage >= len(revealTimings) {
		return nil
	}
	delay := revealTimings[stage]
	return tea.Tick(delay, func(time.Time) tea.Msg { return RevealStageMsg{Stage: stage + 1} })
}

// Init requests the window size, starts the one-shot reveal chain, and begins
// the input cursor blink (the prompt auto-focuses, spec §18.3).
func (m Model) Init() tea.Cmd {
	cmds := []tea.Cmd{
		func() tea.Msg { return tea.RequestWindowSize() },
		m.input.Focus(),
	}
	if !m.noAnimation {
		cmds = append(cmds, revealCmd(0))
	}
	return tea.Batch(cmds...)
}

// Update is the Elm update step: every transition here maps a message to new
// state plus an optional command. View stays pure (§17.4). The textinput and
// spinner are fed every message so their internals (cursor blink, pastes,
// spinner frames) advance correctly; each no-ops on messages it ignores.
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd

	var icmd tea.Cmd
	m.input, icmd = m.input.Update(msg)
	cmds = append(cmds, icmd)

	// The spinner only advances while a state is running; when a phase ends,
	// its in-flight tick is dropped and nothing re-schedules, so idle never
	// redraws (§17.5).
	if m.phase == PhaseSubmitting || m.phase == PhaseRestoring {
		var scmd tea.Cmd
		m.spinner, scmd = m.spinner.Update(msg)
		cmds = append(cmds, scmd)
	}

	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		return m.handleResize(msg, cmds)

	case tea.KeyPressMsg:
		return m.handleKey(msg, cmds)

	case tea.MouseMotionMsg, tea.MouseClickMsg, tea.MouseReleaseMsg, tea.MouseWheelMsg:
		return m.handleMouse(msg, cmds)

	case RevealStageMsg:
		if msg.Stage <= m.reveal {
			return m, tea.Batch(cmds...)
		}
		m.reveal = msg.Stage
		if msg.Stage >= 5 {
			m.phase = PhaseReady
			return m, tea.Batch(cmds...)
		}
		return m, tea.Batch(append(cmds, revealCmd(msg.Stage))...)

	case PulseDoneMsg:
		m.emptyPulse = false
		return m, tea.Batch(cmds...)

	case SubmitResultMsg:
		return m.handleSubmitResult(msg, cmds)

	case RestoreResultMsg:
		return m.handleRestoreResult(msg, cmds)

	case FeedbackDimMsg:
		m.feedbackDimmed = true
		return m, tea.Batch(cmds...)
	}
	return m, tea.Batch(cmds...)
}

func (m Model) handleResize(msg tea.WindowSizeMsg, cmds []tea.Cmd) (tea.Model, tea.Cmd) {
	if msg.Width == m.width && msg.Height == m.height {
		return m, tea.Batch(cmds...) // dedupe: no command backlog on resize floods (§17.5)
	}
	m.width = msg.Width
	m.height = msg.Height
	met := layout.Compute(m.width, m.height)

	// Reconcile the textinput visible width with the prompt box; switch to the
	// short placeholder when the box can't hold the long one (§8.1). The width
	// leaves room for the 2-cell indent plus the cursor, so the rendered input
	// never overflows the box interior (the Box clips as a safety net).
	iw := met.PromptRect.W - 5
	if iw < 10 {
		iw = 10
	}
	m.input.SetWidth(iw)
	if iw < 50 {
		m.input.Placeholder = "Describe a task…"
	} else {
		m.input.Placeholder = "Describe a migration, build, diagnosis, or optimization task…"
	}
	return m, tea.Batch(cmds...)
}

// editable reports whether the prompt accepts typing (spec §8.2: locked while
// submitting/restoring, editable again on ready, feedback and error).
func (m Model) editable() bool {
	return m.phase == PhaseReady || m.phase == PhaseFeedback || m.phase == PhaseError
}

func (m Model) handleKey(msg tea.KeyPressMsg, cmds []tea.Cmd) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "ctrl+c", "ctrl+q":
		return m, tea.Quit
	case "q":
		// q quits only when no input focus (spec §11).
		if m.focus == FocusActions {
			return m, tea.Quit
		}
	}

	switch msg.String() {
	case "enter":
		return m.handleEnter(cmds)
	case "esc":
		if m.editable() {
			return m.handleEsc(cmds)
		}
	case "ctrl+u":
		if m.focus == FocusPrompt && m.editable() {
			m.input.SetValue("")
		}
	case "down":
		if m.focus == FocusActions {
			if m.selected < 2 {
				return m.focusActions(m.selected+1, cmds) // clamp: no wrap (§9.3)
			}
		}
		if m.focus == FocusPrompt && m.phase == PhaseReady {
			return m.focusActions(0, cmds)
		}
	case "tab":
		if m.focus == FocusPrompt && m.phase == PhaseReady {
			return m.focusActions(0, cmds)
		}
		if m.focus == FocusActions {
			return m.focusPrompt(cmds)
		}
	case "up":
		if m.focus == FocusActions {
			if m.selected == 0 {
				return m.focusPrompt(cmds)
			}
			return m.focusActions(m.selected-1, cmds)
		}
	}

	// Plain characters, navigation, etc. were already consumed by the input at
	// the top of Update.
	return m, tea.Batch(cmds...)
}

func (m Model) handleEnter(cmds []tea.Cmd) (tea.Model, tea.Cmd) {
	switch m.phase {
	case PhaseSubmitting, PhaseRestoring, PhaseFeedback:
		return m, tea.Batch(cmds...) // input locked while running
	}
	if m.focus == FocusPrompt {
		if m.input.Value() == "" {
			m.emptyPulse = true
			return m, tea.Batch(append(cmds, tea.Tick(120*time.Millisecond, func(time.Time) tea.Msg { return PulseDoneMsg{} }))...)
		}
		m.errMsg = ""
		m.phase = PhaseSubmitting
		return m, tea.Batch(append(append(cmds, m.spinner.Tick), tea.Tick(450*time.Millisecond, func(time.Time) tea.Msg {
			return SubmitResultMsg{OK: true}
		}))...)
	}
	return m.activateAction(cmds)
}

func (m Model) handleEsc(cmds []tea.Cmd) (tea.Model, tea.Cmd) {
	if m.focus == FocusPrompt {
		if m.input.Value() != "" {
			m.input.SetValue("")
			return m, tea.Batch(cmds...)
		}
		return m.focusActions(0, cmds)
	}
	return m.focusPrompt(cmds)
}

func (m Model) activateAction(cmds []tea.Cmd) (tea.Model, tea.Cmd) {
	switch m.selected {
	case 0: // Migrate: fill prompt, keep editing (spec §9.4)
		m.input.SetValue(components.PrefillMigrate)
		m.input.SetCursor(len([]rune(components.PrefillMigrate)))
		return m.focusPrompt(cmds)
	case 1: // Scan: fill prompt, keep editing
		m.input.SetValue(components.PrefillScan)
		m.input.SetCursor(len([]rune(components.PrefillScan)))
		return m.focusPrompt(cmds)
	default: // Resume: spinner + status, then restored feedback (spec §9.4)
		m.errMsg = ""
		m.phase = PhaseRestoring
		return m, tea.Batch(append(append(cmds, m.spinner.Tick),
			tea.Tick(750*time.Millisecond, func(time.Time) tea.Msg { return RestoreResultMsg{OK: true} }))...)
	}
}

func (m Model) handleSubmitResult(msg SubmitResultMsg, cmds []tea.Cmd) (tea.Model, tea.Cmd) {
	if !msg.OK {
		m.phase = PhaseError
		m.errMsg = msg.Err
		return m, tea.Batch(cmds...)
	}
	m.phase = PhaseFeedback
	m.feedback = "✓ Task captured · Workspace view is the next implementation step"
	m.feedbackDimmed = false
	m.errMsg = ""
	return m, tea.Batch(append(cmds, dimCmd())...)
}

func (m Model) handleRestoreResult(msg RestoreResultMsg, cmds []tea.Cmd) (tea.Model, tea.Cmd) {
	if !msg.OK {
		m.phase = PhaseError
		m.errMsg = msg.Err
		return m, tea.Batch(cmds...)
	}
	m.phase = PhaseFeedback
	m.feedback = "✓ Session restored · Workspace view is the next implementation step"
	m.feedbackDimmed = false
	m.errMsg = ""
	m.restored = true
	return m, tea.Batch(append(cmds, dimCmd())...)
}

func dimCmd() tea.Cmd {
	return tea.Tick(2500*time.Millisecond, func(time.Time) tea.Msg { return FeedbackDimMsg{} })
}

func (m Model) focusActions(sel int, cmds []tea.Cmd) (tea.Model, tea.Cmd) {
	m.focus = FocusActions
	m.selected = sel
	m.hover = -1
	m.input.Blur()
	return m, tea.Batch(cmds...)
}

func (m Model) focusPrompt(cmds []tea.Cmd) (tea.Model, tea.Cmd) {
	m.focus = FocusPrompt
	m.hover = -1
	return m, tea.Batch(append(cmds, m.input.Focus())...)
}

func (m Model) handleMouse(msg tea.Msg, cmds []tea.Cmd) (tea.Model, tea.Cmd) {
	met := layout.Compute(m.width, m.height)
	switch e := msg.(type) {
	case tea.MouseMotionMsg:
		p := e.Mouse()
		idx := met.ActionAt(p.X, p.Y)
		if idx != m.hover {
			m.hover = idx // hover never steals focus (§9.3)
		}
	case tea.MouseClickMsg:
		p := e.Mouse()
		if p.Button != tea.MouseLeft {
			return m, tea.Batch(cmds...)
		}
		if idx := met.ActionAt(p.X, p.Y); idx >= 0 {
			m.selected = idx
			return m.activateAction(cmds) // click selects + activates (§9.3)
		}
		if met.PromptAt(p.X, p.Y) {
			return m.focusPrompt(cmds)
		}
	}
	return m, tea.Batch(cmds...)
}
