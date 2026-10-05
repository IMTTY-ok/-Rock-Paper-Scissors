# Rock Paper Scissors

A rock-paper-scissors game with two front ends sharing one look: a neon cyberpunk
terminal UI and a single-file browser version. No dependencies, no build step, no
backend, no environment variables.

```
✊  ✋  ✌    ROCK PAPER SCISSORS
```

## Play

### Terminal

```bash
python rock_paper_scissors.py
```

### Browser

The browser game is a single self-contained `index.html` at the repository root,
so serve the repository root:

```bash
python -m http.server 8000
```

Then open <http://localhost:8000>

## Controls

| Key | Action |
| --- | --- |
| `1` | Rock |
| `2` | Paper |
| `3` | Scissors |
| `0` / `Q` | Quit |
| `Enter` | Start / rematch |
| `R` | Rematch |

In the terminal you can also type `rock`, `paper`, or `scissors`.

## Modes

At the start of a match, pick a target score: any odd number for first-to-N, or `0`
for endless. The browser version offers first-to-3, first-to-5, and endless.

## Features

- Live score bars, round counter, and win-streak tracking
- Round-by-round history strip
- Animated opponent reveal, win/lose/tie banners, screen shake, and end-of-match stats
- Keyboard and mouse input in the browser
- Responsive layout, verified from 58 to 96 terminal columns

## Requirements

Python 3.6 or newer. Nothing to install.

## Accessibility

- Honors the `NO_COLOR` environment variable and disables color when output is piped
- Respects `prefers-reduced-motion`, skipping animations
- Web version keeps buttons keyboard-reachable with visible focus states

## Terminal options

| Flag | Effect |
| --- | --- |
| `--plain` | Disable all color |
| `--no-motion` | Skip animations |
| `--mute` | Disable sound |

Equivalent environment variables: `RPS_MOTION=0`, `RPS_MUTE=1`, `NO_COLOR=1`.

Color degrades automatically on 256-color terminals, and Windows VT mode plus UTF-8
output are enabled at startup when needed.

## Layout

```
index.html               Browser game (self-contained, at the root on purpose)
rock_paper_scissors.py   Terminal game
```

`index.html` sits at the repository root so that static hosts, including Vercel,
serve it at `/` with no extra configuration.

## Deploying to Vercel

The repository is a static site: no build step, no dependencies, no backend.

| Setting | Value |
| --- | --- |
| Framework Preset | Other |
| Root Directory | `/` (repository root) |
| Build Command | leave empty |
| Output Directory | leave empty (Vercel serves the root) |

## License

[MIT](LICENSE)