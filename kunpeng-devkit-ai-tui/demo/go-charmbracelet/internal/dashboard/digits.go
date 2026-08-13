package dashboard

// heroDigits is the 3×5 pixel font for KPI hero numbers (mirrors Scheme A's
// HERO_DIGITS). Every glyph is width-1 per cell, so hero lines are CJK-safe.
var heroDigits = map[rune][3]string{
	'0': {"█▀█", "█ █", "█▄█"},
	'1': {" ▄█", "  █", " ▄█"},
	'2': {"▀▀█", "█▀▀", "█▄▄"},
	'3': {"▀▀█", " ▀█", "▄▄█"},
	'4': {"█ █", "▀▀█", "  █"},
	'5': {"█▀▀", "▀▀█", "▄▄█"},
	'6': {"█▀▀", "█▀█", "█▄█"},
	'7': {"▀▀█", "  █", "  █"},
	'8': {"█▀█", "█▀█", "█▄█"},
	'9': {"█▀█", "▀▀█", "▄▄█"},
	'.': {"   ", "   ", " ▄ "},
	':': {"   ", " ▄ ", " ▀ "},
}

// heroNumber renders a digit string as three rows of hero glyphs, one space
// between glyphs.
func heroNumber(value string) [3]string {
	rows := [3]string{}
	for _, ch := range value {
		glyph, ok := heroDigits[ch]
		if !ok {
			glyph = heroDigits['0']
		}
		for r := 0; r < 3; r++ {
			if rows[r] != "" {
				rows[r] += " "
			}
			rows[r] += glyph[r]
		}
	}
	return rows
}
