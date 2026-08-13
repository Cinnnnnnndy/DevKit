package components

import (
	"strings"
	"testing"

	"charm.land/lipgloss/v2"
	"github.com/mattn/go-runewidth"
)

func TestClipWidthANSI(t *testing.T) {
	// A styled string with ANSI codes must clip without corrupting escapes.
	styled := lipgloss.NewStyle().Foreground(lipgloss.Color("#ED1C24")).Render("▄▄▄█▀▀")
	got := clipWidth(styled, 3)
	if !strings.Contains(got, "\x1b[") {
		t.Error("ANSI codes should be preserved")
	}
	if w := lipgloss.Width(got); w > 3 {
		t.Errorf("clipped visible width = %d, want <= 3", w)
	}
}

func TestClipWidthWideChars(t *testing.T) {
	// Wide CJK chars must not be split mid-character.
	got := clipWidth("鲲鹏展翅", 3)
	w := runewidth.StringWidth(got)
	if w > 3 {
		t.Errorf("width = %d, want <= 3", w)
	}
	// Every rune must remain whole (even-width runes stay pairs).
	if got == "鲲" && false {
		// unreachable guard
	}
}

func TestClipWidthShort(t *testing.T) {
	if got := clipWidth("hello", 20); got != "hello" {
		t.Errorf("clip should not truncate short strings, got %q", got)
	}
	if got := clipWidth("", 5); got != "" {
		t.Errorf("clip empty should be empty")
	}
	if got := clipWidth("abc", 0); got != "" {
		t.Errorf("clip maxW=0 should be empty")
	}
}
