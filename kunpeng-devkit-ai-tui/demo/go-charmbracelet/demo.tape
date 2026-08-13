# Kunpeng DevKit AI — Scheme B "Charm Flow" demo (spec §19)
# Records at the canonical 156×48 cells (calibrated for SF Mono @16px:
# Set Width 2370 px, Set Height 1079 px, Padding 0).
Output demo.gif
Set FontFamily "SF Mono"
Set FontSize 16
Set Width 2370
Set Height 1079
Set Padding 0
Set Framerate 60
Set PlaybackSpeed 1
Set TypingSpeed 40ms

# 1. Launch entrance (one-shot 420ms reveal, §13.1) — hold ≥800ms to observe
Type "./devkitai"
Enter
Sleep 1800ms

# 2. Type a task into the focused prompt
Type "migrate nginx to Kunpeng ARM64"
Sleep 1800ms

# 3. Clear with Ctrl+U
Ctrl+U
Sleep 1200ms

# 4-5. Navigate to the Scan suggestion
Down
Sleep 1000ms
Down
Sleep 1000ms

# 6. Activate Scan → fills the prompt, focus returns to editing (no auto-submit)
Enter
Sleep 1800ms

# 7. Submit → spinner → success feedback
Enter
Sleep 4000ms

# 8. Trailing hold for review
Sleep 2000ms
