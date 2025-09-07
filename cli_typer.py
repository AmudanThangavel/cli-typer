#!/usr/bin/env python3
# Avoid writing .pyc in restrictive environments
import sys as _sys
_sys.dont_write_bytecode = True

import argparse
import locale
import random
import time
import os
import sys
from dataclasses import dataclass
from typing import List, Optional, Set


# Ensure wide characters render correctly in curses
locale.setlocale(locale.LC_ALL, "")


DEFAULT_WORDS = (
    # A compact set of common English words; extend as needed
    "the of and to in is you that it he was for on are as with his they I at be this have from or one had by word but not what all were we when your can said there use an each which she do how their if"
    " will up other about out many then them these so some her would make like him into time has look two more write go see number no way could people my than first water been call who oil its now find"
    " long down day did get come made may part over new sound take only little work know place year live me back give most very after thing our just name good sentence man think say great where help through"
    " much before line right too means old any same tell boy follow came want show also around form three small set put end does another well large must big even such because turn here why ask went men read"
    " need land different home us move try kind hand picture again change off play spell air away animal house point page letter mother answer found study still learn should America world high every near add food"
    " between own below country plant last school father keep tree never start city earth eye light thought head under story saw left don't few while along might close something seem next hard open example begin"
    " life always those both paper together got group often run important until children side feet car mile night walk white sea began grow took river four carry state once book hear stop without second late miss"
    " idea enough eat face watch far Indian real almost let above girl sometimes mountain cut young talk soon list song being leave family it's body music color stand sun questions fish area mark dog horse birds"
    " problem complete room knew since ever piece told usually didn’t friends easy heard order red door sure become top ship across today during short better best however low hours black products happened whole measure remember"
    " early waves reached listen wind rock space covered fast several hold himself toward five step morning passed vowel true hundred against pattern numeral table north slowly money map farm pulled draw voice seen cold cried"
    " plan notice south sing war ground fall king town I'll unit figure certain field travel wood fire upon done English road halt ten fly gave box finally waited correct oh quickly person became shown minutes"
).split()


NUMBERS = list("0123456789")
PUNCT = list(", . ! ? : ; ' \" - ( ) [ ] { } / \\".split())

# Global keyboard highlight state (can't set attrs on curses windows)
from typing import Set as _SetAlias
_HIGHLIGHT_TOKENS: _SetAlias[str] = set()

def set_highlight_tokens(tokens: _SetAlias[str]):
    global _HIGHLIGHT_TOKENS
    _HIGHLIGHT_TOKENS = set(tokens) if tokens else set()

def get_highlight_tokens() -> _SetAlias[str]:
    return _HIGHLIGHT_TOKENS


@dataclass
class Config:
    mode: str  # "time" or "words"
    seconds: int
    words: int
    numbers: bool
    punctuation: bool
    seed: Optional[int]


@dataclass
class Stats:
    started: Optional[float] = None
    ended: Optional[float] = None
    typed: int = 0
    correct: int = 0
    mistakes: int = 0

    def start(self):
        if self.started is None:
            self.started = time.time()

    def stop(self):
        if self.ended is None:
            self.ended = time.time()

    @property
    def seconds_elapsed(self) -> float:
        if self.started is None:
            return 0.0
        end = self.ended if self.ended is not None else time.time()
        return max(0.0, end - self.started)

    @property
    def minutes_elapsed(self) -> float:
        return self.seconds_elapsed / 60.0

    @property
    def accuracy(self) -> float:
        return 0.0 if self.typed == 0 else self.correct / self.typed

    @property
    def raw_wpm(self) -> float:
        # Raw WPM: correct characters/5 per minute
        if self.minutes_elapsed <= 0:
            return 0.0
        return (self.correct / 5.0) / self.minutes_elapsed


class WordSource:
    def __init__(self, config: Config):
        base = list(DEFAULT_WORDS)
        if config.numbers:
            base += NUMBERS
        if config.punctuation:
            base += PUNCT
        self.words = base
        self.rng = random.Random(config.seed)

    def generate(self, count: int) -> List[str]:
        return [self.rng.choice(self.words) for _ in range(count)]


def wrap_text_to_lines(text: str, width: int) -> List[str]:
    if width <= 0:
        return [text]
    words = text.split(" ")
    lines: List[str] = []
    line = ""
    for w in words:
        # account for space when adding next word
        if not line:
            trial = w
        else:
            trial = line + " " + w
        if len(trial) <= width:
            line = trial
        else:
            if line:
                lines.append(line)
            # If a single word is longer than width, split it
            while len(w) > width:
                lines.append(w[:width])
                w = w[width:]
            line = w
    if line:
        lines.append(line)
    return lines


def build_text(source: WordSource, config: Config) -> str:
    if config.mode == "words":
        count = max(1, config.words)
    else:
        # Time mode: prepare a generous buffer; we will stop by time.
        # Aim roughly for a high WPM upper bound so we don't run out.
        # 200 wpm => 200 * 5 chars/min ~ 1000 chars per 60s. Words ~ 200.
        # Scale by seconds.
        est_words = int(max(50, (config.seconds / 60.0) * 300))
        count = est_words
    return " ".join(source.generate(count))


def draw_text(stdscr, text: str, pos: int, top: int, width: int, height: int):
    # Draw the text with coloring for typed/correct/incorrect and caret
    # Compute visible window region based on current position
    # Keep a margin of a few lines above/below
    max_text_width = max(1, width - 2)
    lines = wrap_text_to_lines(text, max_text_width)
    # Map pos (flat index) to line/col
    flat_to_line = []
    idx = 0
    for li, line in enumerate(lines):
        for ci, ch in enumerate(line):
            flat_to_line.append((li, ci))
            idx += 1
        # account for soft-wrapped spaces; mapping only for characters
        if idx < len(text) and text[idx] == " ":
            # space fits only if not at end of line
            if len(line) < max_text_width:
                flat_to_line.append((li, len(line)))
                idx += 1
        # If the line was hard-wrapped (word split), we didn't consume space

    # Determine scroll offset so caret line stays in view
    caret_line = 0
    if pos < len(flat_to_line):
        caret_line = flat_to_line[pos][0]
    visible_lines = height - top - 3  # leave room for status lines
    scroll = max(0, caret_line - visible_lines // 2)
    # draw
    for i in range(visible_lines):
        y = top + i
        if i + scroll < len(lines):
            stdscr.addnstr(y, 1, lines[i + scroll], max_text_width, curses.color_pair(1))
            # overlay typed regions with correctness colors
        else:
            stdscr.addnstr(y, 1, "".ljust(max_text_width), max_text_width)

    # Overlay correctness
    # Reconstruct same wrapping while painting up to current pos
    draw_idx = 0
    cur_line = 0
    cur_col = 0
    for i, ch in enumerate(text):
        # compute target line and col using wrap
        if cur_line >= scroll and cur_line < scroll + visible_lines:
            y = top + (cur_line - scroll)
            x = 1 + cur_col
            if i < pos:
                # typed
                # Determine if user typed it correctly is handled by caller via attributes; here we only show baseline
                pass
        # advance position in wrapped coords
        # compute next position
        # we need to mirror wrapping logic quickly; simpler approach: use flat_to_line mapping
        if i < len(flat_to_line):
            cur_line, cur_col = flat_to_line[i]
        draw_idx = i
    # We will actually color at input time instead of here for simplicity


def render_screen(stdscr, text: str, typed: List[str], stats: Stats, config: Config):
    import curses
    stdscr.erase()
    height, width = stdscr.getmaxyx()

    # Colors
    default = curses.color_pair(1)
    correct_color = curses.color_pair(2)
    wrong_color = curses.color_pair(3)
    caret_color = curses.color_pair(4)
    dim_color = curses.color_pair(5)
    key_color = curses.color_pair(6)

    # Title
    title = "CLI Typer — ESC: quit  TAB: restart  F2: toggle mode"
    stdscr.addnstr(0, 1, title, width - 2, dim_color)

    # Build the displayed text area
    max_text_width = max(1, width - 2)
    lines = wrap_text_to_lines(text, max_text_width)

    # Draw base text
    # Space for keyboard + status if height allows
    show_keyboard = height >= 16
    kb_rows = get_keyboard_layout()
    kb_height = len(kb_rows) + 1 if show_keyboard else 0
    usable_lines = max(3, height - (kb_height + 5))
    # Determine caret line/scroll
    pos = len(typed)
    # Map flat to line indices to compute caret line
    flat_to_line = []
    idx = 0
    for li, line in enumerate(lines):
        for ci, ch in enumerate(line):
            flat_to_line.append((li, ci))
            idx += 1
        if idx < len(text) and text[idx] == " ":
            if len(line) < max_text_width:
                flat_to_line.append((li, len(line)))
                idx += 1

    caret_line = flat_to_line[pos][0] if pos < len(flat_to_line) else (len(lines) - 1 if lines else 0)
    scroll = max(0, caret_line - usable_lines // 2)

    # Base draw
    for i in range(usable_lines):
        y = 2 + i
        if i + scroll < len(lines):
            stdscr.addnstr(y, 1, lines[i + scroll], max_text_width, default)
        else:
            stdscr.addnstr(y, 1, "".ljust(max_text_width), max_text_width, default)

    # Overlay typed characters with correctness colors
    for i, ch in enumerate(text[: len(typed)]):
        tl, tc = flat_to_line[i] if i < len(flat_to_line) else (len(lines) - 1, 0)
        y = 2 + (tl - scroll)
        x = 1 + tc
        if 2 <= y < 2 + usable_lines:
            if typed[i] == ch:
                stdscr.addnstr(y, x, ch, 1, correct_color)
            else:
                stdscr.addnstr(y, x, ch, 1, wrong_color)

    # Caret position
    if pos < len(text) and pos < len(flat_to_line):
        tl, tc = flat_to_line[pos]
        y = 2 + (tl - scroll)
        x = 1 + tc
        if 2 <= y < 2 + usable_lines:
            caret_ch = text[pos]
            stdscr.addnstr(y, x, caret_ch if caret_ch != " " else "_", 1, caret_color)

    # Status bar
    elapsed = stats.seconds_elapsed
    remaining = max(0, config.seconds - int(elapsed)) if config.mode == "time" else None
    wpm = stats.raw_wpm
    acc = stats.accuracy * 100.0
    status_main = (
        f"Mode: {config.mode}  "
        + (f"Time: {remaining:>3}s  " if remaining is not None else f"Words: {config.words}  ")
        + f"WPM: {wpm:5.1f}  Acc: {acc:5.1f}%"
    )
    stdscr.addnstr(height - 2, 1, status_main.ljust(width - 2), width - 2, dim_color)

    # Keyboard display
    if show_keyboard:
        kb_top = 2 + usable_lines + 1
        render_keyboard(stdscr, kb_top, width, dim_color, key_color)

    stdscr.refresh()


def typing_session(stdscr, config: Config) -> Stats:
    import curses
    curses.curs_set(0)
    stdscr.nodelay(False)
    stdscr.keypad(True)

    # Colors
    curses.use_default_colors()
    curses.init_pair(1, -1, -1)  # default
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_RED, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_BLACK if curses.can_change_color() else curses.COLOR_WHITE, -1)
    curses.init_pair(6, curses.COLOR_YELLOW, -1)  # key highlight

    source = WordSource(config)
    text = build_text(source, config)
    typed: List[str] = []
    stats = Stats()
    set_highlight_tokens(set())

    def finished() -> bool:
        if config.mode == "time":
            return stats.started is not None and stats.seconds_elapsed >= config.seconds
        else:
            return len(typed) >= len(text)

    render_screen(stdscr, text, typed, stats, config)

    while True:
        ch = stdscr.get_wch()
        if ch == "\t":  # restart
            set_highlight_tokens(normalize_key_to_tokens(ch))
            return Stats()  # caller handles restart by new loop
        if ch in ("\x1b", curses.KEY_EXIT):  # ESC
            stats.stop()
            return stats
        if ch == curses.KEY_RESIZE:
            render_screen(stdscr, text, typed, stats, config)
            continue

        if isinstance(ch, str):
            if ch in ("\n", "\r"):
                # treat enter as space
                ch = " "
            if ch == "\x7f" or ch == "\b":  # Backspace
                if typed:
                    # Undo stats for last char
                    last_i = len(typed) - 1
                    if typed[last_i] == text[last_i]:
                        stats.correct = max(0, stats.correct - 1)
                    else:
                        stats.mistakes = max(0, stats.mistakes - 1)
                    stats.typed = max(0, stats.typed - 1)
                    typed.pop()
                    set_highlight_tokens(normalize_key_to_tokens("\b"))
                    render_screen(stdscr, text, typed, stats, config)
                continue

            # filter to printable range; allow spaces
            if ch.isprintable() or ch == " ":
                if stats.started is None and ch.strip() != "":
                    stats.start()
                # append, compare to target if exists
                if len(typed) < len(text):
                    typed.append(ch)
                    stats.typed += 1
                    target_ch = text[len(typed) - 1]
                    if ch == target_ch:
                        stats.correct += 1
                    else:
                        stats.mistakes += 1
                # if we are in time mode and typing past buffer, extend it slightly
                if config.mode == "time" and len(typed) >= len(text) and not finished():
                    # Extend buffer with more words
                    text += " " + " ".join(WordSource(config).generate(50))
                set_highlight_tokens(normalize_key_to_tokens(ch))
                render_screen(stdscr, text, typed, stats, config)

        elif ch in (curses.KEY_BACKSPACE, 127):
            if typed:
                last_i = len(typed) - 1
                if typed[last_i] == text[last_i]:
                    stats.correct = max(0, stats.correct - 1)
                else:
                    stats.mistakes = max(0, stats.mistakes - 1)
                stats.typed = max(0, stats.typed - 1)
                typed.pop()
                set_highlight_tokens(normalize_key_to_tokens(ch))
                render_screen(stdscr, text, typed, stats, config)

        # Check end condition
        if finished():
            stats.stop()
            # Final render with completed status
            render_screen(stdscr, text, typed, stats, config)
            # Show results panel
            height, width = stdscr.getmaxyx()
            res = f"Done — WPM: {stats.raw_wpm:.1f}  Accuracy: {stats.accuracy*100:.1f}%  Time: {stats.seconds_elapsed:.1f}s"
            msg = "Press r to restart, q to quit"
            stdscr.addnstr(height - 4, 1, res.ljust(width - 2), width - 2, curses.color_pair(5))
            stdscr.addnstr(height - 3, 1, msg.ljust(width - 2), width - 2, curses.color_pair(5))
            stdscr.refresh()
            while True:
                k = stdscr.get_wch()
                try:
                    set_highlight_tokens(normalize_key_to_tokens(k))
                except Exception:
                    set_highlight_tokens(set())
                if isinstance(k, str) and k.lower() == "r":
                    return Stats()  # signal restart
                if isinstance(k, str) and k.lower() == "q":
                    return stats
                if k == "\t":
                    return Stats()
                if k in ("\x1b", curses.KEY_EXIT):
                    return stats


# --------------------- Keyboard display helpers ---------------------

def get_keyboard_layout() -> List[List[str]]:
    return [
        ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "Back"],
        ["Tab", "q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[", "]", "\\"],
        ["Caps", "a", "s", "d", "f", "g", "h", "j", "k", "l", ";", "'", "Enter"],
        ["Shift", "z", "x", "c", "v", "b", "n", "m", ",", ".", "/", "Shift"],
        ["Space"],
    ]


SHIFTED_TO_BASE = {
    "~": "`",
    "!": "1",
    "@": "2",
    "#": "3",
    "$": "4",
    "%": "5",
    "^": "6",
    "&": "7",
    "*": "8",
    "(": "9",
    ")": "0",
    "_": "-",
    "+": "=",
    "{": "[",
    "}": "]",
    "|": "\\",
    ":": ";",
    '"': "'",
    "<": ",",
    ">": ".",
    "?": "/",
}


def normalize_key_to_tokens(key) -> Set[str]:
    tokens: Set[str] = set()
    # Curses may deliver strings or special key codes
    if isinstance(key, str):
        if key in ("\x7f", "\b"):
            tokens.add("Back")
            return tokens
        if key in ("\n", "\r"):
            tokens.add("Enter")
            return tokens
        if key == "\t":
            tokens.add("Tab")
            return tokens
        if key == " ":
            tokens.add("Space")
            return tokens
        if len(key) == 1:
            ch = key
            if ch.isalpha():
                if ch.isupper():
                    tokens.add("Shift")
                tokens.add(ch.lower())
                return tokens
            if ch in SHIFTED_TO_BASE:
                tokens.add("Shift")
                tokens.add(SHIFTED_TO_BASE[ch])
                return tokens
            # unshifted punctuation present in layout
            tokens.add(ch)
            return tokens
    else:
        # Key codes (avoid curses constant here)
        if isinstance(key, int) and key in (8, 127, 263):
            tokens.add("Back")
            return tokens
    return tokens


def render_keyboard(stdscr, top: int, width: int, base_color, highlight_color):
    rows = get_keyboard_layout()
    for r_index, row in enumerate(rows):
        # Build widths for tokens with surrounding brackets
        labels = [f"[{t}]" for t in row]
        row_text = " ".join(labels)
        total_width = len(row_text)
        x0 = max(1, (width - total_width) // 2)
        y = top + r_index
        # Draw base row
        stdscr.addnstr(y, x0, row_text, min(total_width, width - x0 - 1), base_color)
        # Highlight last pressed tokens if available via global state
        highlight_tokens: Set[str] = get_highlight_tokens()
        if highlight_tokens:
            # paint each token separately so color applies to its region
            cursor_x = x0
            for t in row:
                label = f"[{t}]"
                span = len(label)
                # Center painting on same coordinates
                if t in highlight_tokens:
                    stdscr.addnstr(y, cursor_x, label, span, highlight_color)
                cursor_x += span + 1  # account for joining space



def run_curses(config: Config):
    try:
        import curses
    except Exception:
        print("Error: failed to import curses. On Windows, install: pip install windows-curses. Run from a real terminal.")
        sys.exit(1)
    def _wrapped(stdscr):
        cur_config = config
        while True:
            stats = typing_session(stdscr, cur_config)
            # If returned stats has no start and no end, it was a restart request immediately
            if stats.started is None and stats.ended is None:
                # restart; continue with same config
                continue
            # Ask for immediate restart?
            # At this point, session ended by quit or post-finish choice.
            # If user pressed restart at result, loop will continue due to typing_session returning empty Stats.
            break

    try:
        curses.wrapper(_wrapped)
    except curses.error as e:
        print("Curses error:", e)
        print("Make sure you're running in a real TTY with TERM set (e.g., xterm-256color).")
        sys.exit(1)


def self_check() -> int:
    # Non-interactive validation for CI/sandboxes without TTY
    cfg = Config(mode="time", seconds=10, words=20, numbers=True, punctuation=True, seed=42)
    ws = WordSource(cfg)
    txt = build_text(ws, cfg)
    assert isinstance(txt, str) and len(txt) > 0
    wrapped = wrap_text_to_lines(txt, 20)
    assert all(isinstance(l, str) for l in wrapped)
    s = Stats()
    s.start()
    for ch in txt[:30]:
        s.typed += 1
        s.correct += 1
    time.sleep(0.02)
    s.stop()
    print("CHECK OK — WPM:", f"{s.raw_wpm:.1f}")
    return 0


def parse_args() -> Config:
    p = argparse.ArgumentParser(
        prog="cli-typer",
        description="A terminal typing practice tool (curses-based)",
    )
    p.add_argument("--mode", choices=["time", "words"], default="time", help="Practice mode: time (default) or words")
    p.add_argument("--seconds", type=int, default=60, help="Seconds for time mode (default 60)")
    p.add_argument("--words", type=int, default=50, help="Word count for words mode (default 50)")
    p.add_argument("--numbers", action="store_true", help="Include digits 0-9 in the word pool")
    p.add_argument("--punctuation", action="store_true", help="Include basic punctuation in the word pool")
    p.add_argument("--seed", type=int, default=None, help="Random seed for reproducible word sequences")
    p.add_argument("--check", action="store_true", help="Run a non-interactive self-check and exit")
    args = p.parse_args()
    return Config(
        mode=args.mode,
        seconds=max(5, args.seconds),
        words=max(1, args.words),
        numbers=args.numbers,
        punctuation=args.punctuation,
        seed=args.seed,
    )


def main():
    config = parse_args()
    # Allow running a sandbox-friendly check
    if '--check' in sys.argv:
        raise SystemExit(self_check())
    # Basic TTY/TERM checks
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        print("This program must run in a terminal (TTY). Try running from a proper shell, not an IDE run button.")
        sys.exit(1)
    if not os.environ.get("TERM"):
        os.environ["TERM"] = "xterm-256color"
    run_curses(config)


if __name__ == "__main__":
    main()
