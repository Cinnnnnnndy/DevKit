// Package theme defines the Scheme B "Charm Flow" color tokens and style
// builders. Tokens come from spec_B.md §5.1; degradation rules from §5.4.
package theme

// Palette holds the color tokens. All values are hex strings as authored for
// True Color; the terminal renderer downsamples for 256/16-color profiles.
type Palette struct {
	BgBase             string
	BgSurface          string
	BgSurfaceHover     string
	BgSurfaceActive    string
	BorderSubtle       string
	BorderStrong       string
	TextPrimary        string
	TextSecondary      string
	TextMuted          string
	TextDisabled       string
	Brand              string
	BrandMarkSecondary string
	AccentPink         string
	AccentPurple       string
	AccentCyan         string
	StateSuccess       string
	StateWarning       string
	StateDanger        string
}

// Default is the canonical Scheme B palette (spec §5.1).
var Default = Palette{
	BgBase:             "#181822",
	BgSurface:          "#20202B",
	BgSurfaceHover:     "#282836",
	BgSurfaceActive:    "#303043",
	BorderSubtle:       "#343445",
	BorderStrong:       "#54546A",
	TextPrimary:        "#F4F4F5",
	TextSecondary:      "#B0AFBE",
	TextMuted:          "#77778A",
	TextDisabled:       "#555568",
	Brand:              "#ED1C24",
	BrandMarkSecondary: "#C9C9C9",
	AccentPink:         "#FF5FA2",
	AccentPurple:       "#9B7BFF",
	AccentCyan:         "#5DE4E7",
	StateSuccess:       "#73DACA",
	StateWarning:       "#FFC777",
	StateDanger:        "#FF6B8A",
}

// ActionState is the visual state of a suggestion action row (spec §9.2).
type ActionState int

const (
	ActionIdle ActionState = iota
	ActionHover
	ActionSelected
	ActionPressed
	ActionDisabled
)

// StatusKind identifies the semantic kind of an environment status item.
type StatusKind int

const (
	StatusRuntime StatusKind = iota
	StatusMCP
	StatusARM64
)
