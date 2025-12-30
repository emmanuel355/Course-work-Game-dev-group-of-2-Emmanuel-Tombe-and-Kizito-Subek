Cyber Serpent — Game README

Overview
- Title: Cyber Serpent: Neon Nexus
- Files: `brick_breaker3.py` (main game), `scripts/generate_sounds.py` (optional sound generator), `assets/sounds/` (SFX/BGM).
- Theme: neon/cyberpunk snake-like arcade with orbs, powerups, obstacles.

Requirements
- Python 3.8+ (use the project's virtualenv if available).
- Pygame installed (pip install pygame).

Quick setup
1. Create/activate a virtualenv (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt  # or `pip install pygame`
```

2. (Optional) Generate placeholder sounds if you want audio:

```powershell
& C:/path/to/your/python.exe scripts/generate_sounds.py
```
This writes WAV/MP3 files into `assets/sounds/`.

Run the game

```powershell
& C:/Users/HP/.virtualenvs/storefront-qOrq4PPp/Scripts/python.exe c:/wamp64/www/portfolio/brick_breaker3.py
```
Or with your Python/venv `python brick_breaker3.py`.

Window and controls
- The game window is resizable and can be maximized. The layout recalculates on resize.
- Controls:
  - Arrow keys: move serpent
  - SPACE: pause/resume (in menu, starts game)
  - ESC: return to menu / exit instructions
  - R: restart level (when paused)

Gameplay notes
- Orbs spawn away from the outermost grid cells so they are reachable (fixes unreachable food at edges).
- HUD occupies the top area; grid scales to fit the window while preserving cell size.
- Obstacles and moving obstacles are placed avoiding the serpent's immediate area.

Audio
- Audio is optional. If `pygame.mixer` fails to initialize, the game will continue without sound.
- Place sounds in `assets/sounds/` (names used by the game: `paddle_hit.wav`, `brick_hit.wav`, `life_lost.wav`, `level_complete.wav`, `menu_select.wav`, `bgm.wav` or `bgm.mp3`).
- Use `scripts/generate_sounds.py` to create placeholder WAVs.

Troubleshooting
- If the game hangs while creating fonts (long SysFont enumeration), the code has been updated to use safe bundled fonts for main UI elements. If you still see font-related delays, ensure your environment's font config is not blocked and try running in a different terminal.
- If the window doesn't resize properly after maximizing, ensure your Pygame build supports `pygame.VIDEORESIZE` (most desktop installations do).
- If audio doesn't play, check that your Python has access to an audio device and `pygame.mixer` initialized. The game will print a warning if mixer initialization fails.

Contributing
- To change layout or grid size, adjust `GRID_WIDTH`, `GRID_HEIGHT`, and `CELL_SIZE` calculations in `brick_breaker3.py` and test resize behavior.
- To add new orb types, extend `FOOD_COLORS`, add symbol mapping in `EnergyOrb.draw`, and update spawn logic.

License
- Use and modify as you like. No external dependencies beyond Pygame.

If you'd like, I can also create a small `requirements.txt` and add a one-line launcher script. Let me know which you'd prefer next.
