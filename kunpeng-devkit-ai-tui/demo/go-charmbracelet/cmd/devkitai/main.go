// devkitai is the Scheme B "Charm Flow" Launch screen (Go + Bubble Tea v2).
package main

import (
	"flag"
	"fmt"
	"os"

	"charm.land/bubbletea/v2"

	"devkitai/internal/app"
)

func main() {
	noAnim := flag.Bool("no-animation", false, "disable the entrance animation (reduced motion, spec §13.4)")
	flag.Parse()

	p := tea.NewProgram(app.New(*noAnim))
	if _, err := p.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "devkitai: %v\n", err)
		os.Exit(1)
	}
}
