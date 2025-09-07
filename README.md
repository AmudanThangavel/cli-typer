CLI Typer

[![CI](https://github.com/AmudanThangavel/cli-typer/actions/workflows/ci.yml/badge.svg)](https://github.com/AmudanThangavel/cli-typer/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/cli-typer.svg)](https://pypi.org/project/cli-typer/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A fast, curses-based typing practice tool for your terminal — no browser, no accounts. Inspired by monkeytype-style flows, it highlights correct/incorrect characters as you type and shows live WPM and accuracy. Includes an optional on‑screen keyboard overlay that lights up the last key pressed.

Features

- Live WPM and accuracy while you type
- Time and word‑count practice modes
- Optional numbers and punctuation in the word pool
- On‑screen keyboard overlay with key highlights (auto-hides on small terminals)
- Respects terminal size; smooth scrolling keeps the caret in view
- Reproducible word sequences via `--seed`
- Works fully offline; no network calls

Requirements

- Python 3.8+
- Linux/macOS terminal with curses available
- Windows: install `windows-curses` first — `pip install windows-curses`

Install

Option A — pip/pipx (after PyPI release)

- `pipx install cli-typer`
- or `pip install -U cli-typer`

Option B — Homebrew (tap)

- `brew tap AmudanThangavel/tap`
- `brew install cli-typer`

Option C — Clone and run

1) `git clone https://github.com/AmudanThangavel/cli-typer.git`
2) `cd cli-typer`
3) `python3 cli_typer.py`

Quick sandbox check

- `python3 cli_typer.py --check` — runs a small self‑test without curses/TTY

Quick Start

- Run: `python3 cli_typer.py`
- Quit: `ESC`
- Restart: `TAB` or press `r` after a run
- On‑screen keyboard: shows at the bottom (if terminal is tall enough) and highlights the last key pressed

Usage

`python3 cli_typer.py [--mode {time,words}] [--seconds N] [--words N] [--numbers] [--punctuation] [--seed N]`

Examples

- 60‑second time trial (default): `python3 cli_typer.py --mode time --seconds 60`
- 30‑second sprint with punctuation: `python3 cli_typer.py --mode time --seconds 30 --punctuation`
- 100 words, include digits: `python3 cli_typer.py --mode words --words 100 --numbers`
- Reproducible session: `python3 cli_typer.py --seed 1234`

Options

- `--mode {time,words}` — practice by time or by fixed number of words
- `--seconds N` — time (in seconds) for time mode (default 60)
- `--words N` — word count for words mode (default 50)
- `--numbers` — include digits 0–9 in the pool
- `--punctuation` — include basic punctuation in the pool
- `--seed N` — deterministic word order for repeatable practice

Key Bindings

- Type to input characters; correct/incorrect highlights update live
- Backspace — delete previous character (stats adjust accordingly)
- Enter — treated as a space
- `ESC` — quit any time
- `TAB` — restart the session
- After finishing, `r` restarts and `q` quits

Metrics

- WPM (raw): correct characters / 5 per minute
- Accuracy: correct characters / total typed

Demo (ASCII)

```
CLI Typer — ESC: quit  TAB: restart  F2: toggle mode

the quick brown fox jumps over the lazy dog
the quick brown fux jumps over the lazy dog
                                 ^

Mode: time  Time:  58s  WPM:  92.4  Acc:  97.8%

[`][1][2][3][4][5][6][7][8][9][0][-][=][Back]
[Tab][q][w][e][r][t][y][u][i][o][p][[][\]][\]
[Caps][a][s][d][f][g][h][j][k][l][;]['][Enter]
[Shift][z][x][c][v][b][n][m][,][.][/][Shift]
[Space]
```

Troubleshooting

- “curses error / terminal not found” — Run from a real terminal (TTY), not an IDE “Run” button. Ensure `TERM` is set, e.g., `export TERM=xterm-256color`.
- Windows — Install `windows-curses` with `pip install windows-curses`.
- Permissions writing `__pycache__` — The app disables bytecode writes in restrictive environments.

Development

- Code: single file `cli_typer.py` using Python `curses`
- Local run: `python3 cli_typer.py`
- Self‑test: `python3 cli_typer.py --check`
- Style: standard Python 3.8+ typing; no external deps

Contributing

- Issues and PRs are welcome. Please include a clear description and steps to reproduce.
- Ideas: custom word lists, lessons, per‑key accuracy, history/stats logging, color themes, a hotkey to toggle the on‑screen keyboard.

Roadmap

- Toggle on‑screen keyboard (hotkey) and compact mode
- Custom word lists and JSON import
- Save run history as JSON/CSV with timestamps
- Per‑key stats and heatmap
- Configurable color themes
- Packaging to `pip` with a console script entry point (`cli-typer`)

License

- MIT — see [LICENSE](LICENSE)
