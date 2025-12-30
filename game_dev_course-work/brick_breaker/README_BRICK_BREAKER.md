Castle Defender — Brick Breaker (README)

File: `brick_breaker.py`

Overview
- Single-file Pygame brick-breaker style game with enhanced visuals, multiple levels, and optional sound.
- Features: menu, instructions, pause, level complete, background music and SFX (optional), safe font fallback to avoid font enumeration hangs.

Requirements
- Python 3.8+ recommended.
- Pygame installed: `pip install pygame`.

Optional
- Virtual environment recommended.
- Audio: Having a working audio device and `pygame.mixer` will enable background music and SFX.

Key files
- `brick_breaker2.py` — main game file (this README describes this file).
- `assets/sounds/` — optional sound files (names used: `paddle_hit.wav`, `brick_hit.wav`, `life_lost.wav`, `level_complete.wav`, `menu_select.wav`, `bgm.wav` or `bgm.mp3`).
- `scripts/generate_sounds.py` — helper to synthesize placeholder WAV files (optional).

Run
1. (Optional) create and activate a virtualenv:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install pygame
```

2. Run the game:

```powershell
python brick_breaker2.py
```
Or, if you use a specific Python/virtualenv path, call that interpreter instead.

Controls
- LEFT / RIGHT arrows: move paddle
- SPACE: launch (when ready), pause/resume during play
- ESC: return to menu

Notes and important implementation details
- Font handling: to avoid long blocking calls during system font enumeration, the code uses a `safe_font()` helper which prefers a bundled/default font (`pygame.font.Font(None, size)`) and sets bold where requested. This prevents the program from hanging when `pygame.font.SysFont(...)` can be slow on some systems.

- Audio: mixer initialization is attempted at startup; if it fails, the game continues without sound and prints a warning. Background music is played when gameplay state is active and stopped otherwise.

- READY state: after pressing Start the game enters a READY state so the player can press SPACE to launch the ball. This addresses UX where the ball would immediately start.

Troubleshooting
- If the game crashes or hangs at font creation: ensure Pygame is properly installed. The code uses safe fallbacks, but some environments still experience font issues — try running in a fresh virtualenv.
- If audio does not play: ensure your system has an audio device and `pygame.mixer` can initialize; check console output for the mixer-initialization warning.
- If the window is too small or fonts appear large/small: adjust display scaling or run in a larger window; the game uses fixed resolution layout (800x600 by default).

Development notes
- To add or replace sounds, drop appropriately named files into `assets/sounds/`.
- UI fonts and sizes are centralized in the file — change font sizes carefully to avoid layout overflow.

Want a requirements file (`requirements.txt`) or a small PowerShell launcher script? I can add those next.
