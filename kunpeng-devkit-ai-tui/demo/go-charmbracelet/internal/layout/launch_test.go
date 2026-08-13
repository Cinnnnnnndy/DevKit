package layout

import "testing"

func TestComputeDual(t *testing.T) {
	m := Compute(156, 48)
	if m.Tier != TierDual {
		t.Fatalf("tier = %v, want dual", m.Tier)
	}
	if m.CW != 104 || m.CH != 20 {
		t.Errorf("content = %dx%d, want 104x20", m.CW, m.CH)
	}
	if m.RightW != 65 {
		t.Errorf("rightW = %d, want 65", m.RightW)
	}
	if m.CX != 26 {
		t.Errorf("CX = %d, want 26", m.CX)
	}
	if m.PromptRect.X != 26+33+6 {
		t.Errorf("prompt X = %d, want %d", m.PromptRect.X, 26+33+6)
	}
}

func TestComputeCompactDual(t *testing.T) {
	m := Compute(120, 36)
	if m.Tier != TierDual {
		t.Fatalf("tier = %v, want dual", m.Tier)
	}
	if m.Gap != 4 {
		t.Errorf("gap = %d, want 4 for 120 cols", m.Gap)
	}
}

func TestComputeSingle(t *testing.T) {
	m := Compute(100, 32)
	if m.Tier != TierSingle {
		t.Fatalf("tier = %v, want single", m.Tier)
	}
	if m.RightW != 68 {
		t.Errorf("rightW = %d, want 68", m.RightW)
	}
	if m.Tight {
		t.Error("100x32 should not be tight")
	}
}

func TestComputeMinSingle(t *testing.T) {
	m := Compute(80, 24)
	if m.Tier != TierSingle {
		t.Fatalf("tier = %v, want single", m.Tier)
	}
	if !m.Tight {
		t.Error("80x24 should be tight")
	}
	if m.ActionRects[2].H != 1 {
		t.Errorf("resume rect height = %d, want 1 (collapsed)", m.ActionRects[2].H)
	}
}

func TestComputeTooSmall(t *testing.T) {
	if m := Compute(68, 20); m.Tier != TierTooSmall {
		t.Errorf("68x20 tier = %v, want tooSmall", m.Tier)
	}
	if m := Compute(60, 30); m.Tier != TierTooSmall {
		t.Errorf("60x30 tier = %v, want tooSmall (width)", m.Tier)
	}
	if m := Compute(100, 18); m.Tier != TierTooSmall {
		t.Errorf("100x18 tier = %v, want tooSmall (height)", m.Tier)
	}
}

func TestActionHitTesting(t *testing.T) {
	m := Compute(156, 48)
	// Every point inside an action rect maps to its index.
	for i, r := range m.ActionRects {
		if got := m.ActionAt(r.X+1, r.Y); got != i {
			t.Errorf("ActionAt(%d,%d) = %d, want %d", r.X+1, r.Y, got, i)
		}
		if got := m.ActionAt(r.X+r.W-1, r.Y+r.H-1); got != i {
			t.Errorf("ActionAt(right edge) = %d, want %d", got, i)
		}
	}
	// A point in the prompt is not an action.
	if got := m.ActionAt(m.PromptRect.X+1, m.PromptRect.Y+1); got != -1 {
		t.Errorf("ActionAt(prompt) = %d, want -1", got)
	}
	if !m.PromptAt(m.PromptRect.X+1, m.PromptRect.Y+1) {
		t.Error("PromptAt should hit inside the prompt rect")
	}
	if m.PromptAt(1, 1) {
		t.Error("PromptAt should miss the top-left corner")
	}
}
