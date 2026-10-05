"""RPS ARENA - a neon cyberpunk terminal rock/paper/scissors game.

Pure standard library. Design tokens follow the ui-ux-pro-max design system
(brutalist + cyberpunk-ui): violet primary #7C3AED, rose accent #F43F5E,
neon green #00FF00, neon cyan #00FFFF on a #0F0F23 backdrop, sharp corners,
visible borders, bold type, and a reduced-motion escape hatch.
"""

import os
import random
import re
import shutil
import sys
import time
import unicodedata

# --------------------------------------------------------------------------
# design tokens
# --------------------------------------------------------------------------

BG = "#0F0F23"
FG = "#E2E8F0"
CARD = "#1E1C35"
MUTED = "#94A3B8"
BORDER = "#4C1D95"
PRIMARY = "#7C3AED"
SECONDARY = "#A78BFA"
ACCENT = "#F43F5E"
DESTRUCTIVE = "#EF4444"
NEON_GREEN = "#00FF00"
NEON_CYAN = "#00FFFF"
NEON_MAGENTA = "#FF00FF"
AMBER = "#FFB800"

BAR_FULL = "\u2588"
BAR_EMPTY = "\u2591"
SPARK = ".:*+*:.=*+-*^"

# --------------------------------------------------------------------------
# block font (3 rows x 5 cols per glyph)
# --------------------------------------------------------------------------

FONT = {
    "A": ("\u2588\u2588\u2588 ", "\u2588   \u2588", "\u2588\u2588\u2588\u2588\u2588"),
    "B": ("\u2588\u2588\u2588\u2588 ", "\u2588   \u2588", "\u2588\u2588\u2588\u2588 "),
    "C": (" \u2588\u2588\u2588\u2588", "\u2588    ", " \u2588\u2588\u2588\u2588"),
    "D": ("\u2588\u2588\u2588\u2588 ", "\u2588   \u2588", "\u2588\u2588\u2588\u2588 "),
    "E": ("\u2588\u2588\u2588\u2588\u2588", "\u2588    ", "\u2588\u2588\u2588\u2588 "),
    "F": ("\u2588\u2588\u2588\u2588\u2588", "\u2588    ", "\u2588    "),
    "H": ("\u2588   \u2588", "\u2588\u2588\u2588\u2588\u2588", "\u2588   \u2588"),
    "I": ("\u2588\u2588\u2588\u2588\u2588", "  \u2588  ", "\u2588\u2588\u2588\u2588\u2588"),
    "L": ("\u2588    ", "\u2588    ", "\u2588\u2588\u2588\u2588\u2588"),
    "M": ("\u2588   \u2588", "\u2588\u2588 \u2588\u2588", "\u2588   \u2588"),
    "N": ("\u2588   \u2588", "\u2588\u2588  \u2588", "\u2588 \u2588 \u2588"),
    "O": (" \u2588\u2588\u2588 ", "\u2588   \u2588", " \u2588\u2588\u2588 "),
    "P": ("\u2588\u2588\u2588\u2588 ", "\u2588   \u2588", "\u2588\u2588\u2588\u2588 "),
    "R": ("\u2588\u2588\u2588\u2588 ", "\u2588   \u2588", "\u2588  \u2588 "),
    "S": (" \u2588\u2588\u2588\u2588", " \u2588   ", "\u2588\u2588\u2588\u2588 "),
    "T": ("\u2588\u2588\u2588\u2588\u2588", "  \u2588  ", "  \u2588  "),
    "U": ("\u2588   \u2588", "\u2588   \u2588", " \u2588\u2588\u2588 "),
    "V": ("\u2588   \u2588", "\u2588   \u2588", " \u2588\u2588\u2588 "),
    "W": ("\u2588   \u2588", "\u2588 \u2588 \u2588", "\u2588\u2588 \u2588\u2588"),
    "Y": ("\u2588   \u2588", " \u2588\u2588\u2588 ", "  \u2588  "),
    "0": (" \u2588\u2588\u2588 ", "\u2588 \u2588 \u2588", " \u2588\u2588\u2588 "),
    "1": ("  \u2588  ", " \u2588\u2588  ", " \u2588\u2588\u2588 "),
    "2": ("\u2588\u2588\u2588 ", "   \u2588   ", "\u2588\u2588\u2588\u2588\u2588"),
    "3": ("\u2588\u2588\u2588 ", "   \u2588   ", "\u2588\u2588\u2588 "),
}
HAND = {"rock": "\u270A", "paper": "\u270B", "scissors": "\u270C"}


def logo(screen):
    """Hand symbols plus a wordmark, wrapped onto two lines if space is tight."""
    hands = "  ".join(
        screen.paint(HAND[move], fg=color, bold=True)
        for move, color in zip(ORDER, (NEON_GREEN, NEON_CYAN, ACCENT))
    )
    wordmark = screen.paint("ROCK PAPER SCISSORS", FG, bold=True)
    inner = screen.width - 2
    if visible_len(hands) + 4 + 19 <= inner:
        return [_pad(hands + "    " + wordmark, inner, "center")]
    return [
        _pad(hands, inner, "center"),
        _pad(wordmark, inner, "center"),
    ]


def big_text(word):
    """Render word with the 3-row block font."""
    rows = ["", "", ""]
    for char in word.upper():
        glyph = FONT.get(char)
        if glyph is None:
            glyph = ("     ",) * 3
        for i in range(3):
            rows[i] += glyph[i] + " "
        for i in range(3):
            rows[i] = rows[i][:-1]
    return [row.rstrip() for row in rows]


# --------------------------------------------------------------------------
# moves
# --------------------------------------------------------------------------

ART_W = 12

NUMBERS = {"1": "rock", "2": "paper", "3": "scissors"}
BEATS = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
ORDER = ("rock", "paper", "scissors")


# --------------------------------------------------------------------------
# terminal capability detection
# --------------------------------------------------------------------------


def _enable_windows_vt():
    """Turn on ANSI escape handling for legacy Windows consoles."""
    try:
        import ctypes

        kernel = ctypes.windll.kernel32
        kernel.GetStdHandle.restype = ctypes.c_void_p
        kernel.GetStdHandle.argtypes = [ctypes.c_uint32]
        kernel.GetConsoleMode.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
        kernel.SetConsoleMode.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        handle = kernel.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if not kernel.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel.SetConsoleMode(handle, mode.value | 0x0004))
    except Exception:
        return False


def _force_utf8(stream):
    """Windows consoles default to a legacy codepage; the art needs UTF-8."""
    encoding = (getattr(stream, "encoding", "") or "").lower().replace("-", "")
    if encoding in ("utf8", "utf16", "utf32", "cp65001"):
        return
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
VARIATION_SELECTORS = ("\uFE0E", "\uFE0F")


def visible_len(text):
    """Printable width: ignores ANSI escapes, zero-width selectors, and
    counts East-Asian wide glyphs (the hand symbols) as two columns."""
    width = 0
    for char in ANSI_RE.sub("", text):
        if char in VARIATION_SELECTORS or unicodedata.combining(char):
            continue
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width


def _pad(text, width, align="left"):
    """Pad an already-coloured string to a visible width."""
    gap = max(0, width - visible_len(text))
    if align == "right":
        return " " * gap + text
    if align == "center":
        left = gap // 2
        return " " * left + text + " " * (gap - left)
    return text + " " * gap


def _nearest_256(r, g, b):
    """Map a 24-bit colour onto the xterm-256 palette index."""
    if r == g == b:
        greys = (
            0, 8, 18, 28, 38, 49, 59, 69, 79, 89, 99,
            109, 119, 129, 139, 149, 159, 169, 179, 189, 199, 209, 219, 229, 239,
        )
        return min(greys, key=lambda level: abs(level - r))

    def cube(value):
        return max(0, min(5, round((value - 55) / 40)))

    return 16 + 36 * cube(r) + 6 * cube(g) + cube(b)


class Screen:
    """Small capability-aware rendering surface."""

    def __init__(self, plain=False, no_motion=False, mute=False):
        self.tty = sys.stdout.isatty()
        self.color = not plain and not os.environ.get("NO_COLOR") and self.tty
        if self.color and os.name == "nt":
            self.color = _enable_windows_vt()
        term = os.environ.get("TERM", "")
        self.truecolor = self.color and (
            os.environ.get("COLORTERM", "").startswith("truecolor") or "truecolor" in term
        )
        if self.color:
            self.motion = not no_motion and os.environ.get("RPS_MOTION") != "0"
            self.sound = not mute and os.environ.get("RPS_MUTE") != "1"
        else:
            self.motion = False
            self.sound = False
        self.width = max(58, min(96, shutil.get_terminal_size((80, 24)).columns))
        self._cursor_hidden = False
        _force_utf8(sys.stdout)

    # -- colour helpers ---------------------------------------------------

    def _rgb(self, value, base):
        r, g, b = int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16)
        if self.truecolor:
            return f"{base}2;{r};{g};{b}"
        return f"{base}5;{_nearest_256(r, g, b)}"

    def paint(self, text, fg=None, bg=None, bold=False, dim=False):
        if not self.color:
            return text
        codes = []
        if bold:
            codes.append("1")
        if dim:
            codes.append("2")
        if fg:
            codes.append(self._rgb(fg, "38;"))
        if bg:
            codes.append(self._rgb(bg, "48;"))
        return f"\x1b[{';'.join(codes)}m{text}\x1b[0m" if codes else text

    

    # -- output helpers ---------------------------------------------------

    def write(self, text=""):
        sys.stdout.write(text)
        sys.stdout.flush()

    def line(self, text=""):
        self.write(text + "\n")

    def clear(self):
        self.write("\x1b[2J\x1b[H")

    def hide_cursor(self):
        if self.color and not self._cursor_hidden:
            self.write("\x1b[?25l")
            self._cursor_hidden = True

    def show_cursor(self):
        if self._cursor_hidden:
            self.write("\x1b[?25h")
            self._cursor_hidden = False

    def sleep(self, seconds):
        if self.motion:
            time.sleep(seconds)

    def beat(self, fps=24, frames=10, on_frame=None):
        """Advance n animation frames, calling on_frame(index) each time."""
        if self.motion:
            for i in range(frames):
                on_frame(i)
                time.sleep(1.0 / fps)
        else:
            on_frame(frames - 1)

    def bell(self, tone=None):
        if not self.sound:
            return
        self.write("\a")
        if tone:
            try:
                import winsound

                winsound.Beep(*tone)
            except Exception:
                pass

    # -- primitives -------------------------------------------------------

    def bar(self, ratio, width):
        filled = max(0, min(width, round(ratio * width)))
        return self.paint(BAR_FULL * filled, fg=ACCENT, bg=CARD) + self.paint(
            BAR_EMPTY * (width - filled), fg=BORDER, bg=CARD
        )

    def frame(self, lines, color=BORDER, fill=BG, inset=1):
        """Draw a hard-edged brutalist box around pre-rendered lines."""
        inner = self.width - 2
        body = []
        for raw in lines:
            body.append(
                self.paint(" " * inset + _pad(raw, inner - inset * 2), bg=fill) + " " * inset
            )
        top = self.paint("\u250c" + "\u2500" * inner + "\u2510", fg=color, bold=True)
        bottom = self.paint("\u2514" + "\u2500" * inner + "\u2518", fg=color, bold=True)
        mid = self.paint("\u2502", fg=color) + " " * inner + self.paint("\u2502", fg=color)
        self.line(top)
        for row in body:
            self.line(self.paint("\u2502", fg=color) + row + self.paint("\u2502", fg=color))
        self.line(bottom)

    def title_bar(self, label, color=PRIMARY):
        inner = self.width - 2
        text = f" {label} "
        left = 2
        right = inner - left - len(text)
        self.line(
            self.paint("\u250c" + "\u2500" * left, fg=color, bold=True)
            + self.paint(text, fg=color, bg=CARD, bold=True)
            + self.paint("\u2500" * max(0, right) + "\u2510", fg=color, bold=True)
        )


# --------------------------------------------------------------------------
# move helpers
# --------------------------------------------------------------------------


MOVE_COLOR = {"rock": NEON_GREEN, "paper": NEON_CYAN, "scissors": ACCENT}





def card_cell(move, screen, cursor=None):
    """One card: hand glyph, hotkey, and the move name."""
    color = MOVE_COLOR[move]
    active = cursor == move
    cells = [_pad(screen.paint(HAND[move], fg=color, bold=True), ART_W, "center")]
    cells.append(_pad(screen.paint(f"[{move}]", fg=color, bold=True), ART_W, "center"))
    cells.append(
        _pad(screen.paint(move.upper(), fg=FG if active else MUTED, bold=active), ART_W, "center")
    )
    cells.append(" " * ART_W)
    return cells


def cards_screen(screen, cursor=None):
    """Three move cards laid out side by side inside one hard frame."""
    card_w = ART_W + 2
    columns = [card_cell(move, screen, cursor) for move in ORDER]
    body = [
        "  ".join(columns[c][i] if i < len(columns[c]) else " " * ART_W for c in range(3))
        for i in range(4)
    ]
    screen.frame(body, color=BORDER, fill=CARD)


# --------------------------------------------------------------------------
# ui screens
# --------------------------------------------------------------------------

BOOT_LOG = (
    "mounting /dev/rng .............. OK",
    "loading arena kernel v9.1.7 ..... OK",
    "calibrating gesture matrix ...... OK",
    "handshaking opponent AI ......... OK",
    "scrambling sign cipher .......... OK",
)


def boot(screen):
    screen.clear()
    for row in logo(screen):
        screen.line(row)
    screen.line()
    for entry in BOOT_LOG:
        screen.write(screen.paint("  [", fg=MUTED) + screen.paint(entry, fg=NEON_GREEN))
        if screen.motion:
            screen.write("\r\x1b[K")
            time.sleep(0.05 + random.random() * 0.04)
        screen.line()

    def progress(step):
        screen.write("\r" + screen.paint("  [", fg=MUTED) + screen.paint("loading", fg=MUTED))
        screen.write(screen.paint(BAR_FULL * step, fg=NEON_CYAN))
        screen.write(screen.paint(BAR_EMPTY * (10 - step), fg=BORDER))
        screen.write(screen.paint(f"] {step * 10}%", fg=MUTED) + " ")

    screen.beat(fps=18, frames=10, on_frame=lambda i: progress(i + 1))
    screen.line()
    screen.line()


def hud(screen, state, target):
    inner = screen.width - 4
    you = state["player"]
    bot = state["computer"]
    gap = inner - 32

    header = _pad(screen.paint(" YOU", fg=NEON_GREEN, bold=True), 15)
    header += _pad(screen.paint(f"ROUND {state['rounds'] + 1}", fg=FG, bold=True), gap + 2, "center")
    header += _pad(screen.paint("CPU", fg=NEON_MAGENTA, bold=True), 15, "right")

    scale = target or max(you, bot, 1)
    you_bar = screen.paint(f"{you:>3} ", fg=FG, bold=True) + screen.bar(you / scale, 9)
    bot_bar = screen.paint(f"{bot:>3} ", fg=FG, bold=True) + screen.bar(bot / scale, 9)
    mid = " " * max(2, (gap + 2 - 26) // 2)

    streak = state["streak"]
    if streak >= 2:
        streak_line = screen.paint(
            f"  STREAK x{streak} \u00b7 {BEATS[state['last']]} was right", fg=AMBER, bold=True
        )
    else:
        streak_line = screen.paint("  STREAK x0", fg=MUTED)

    target_line = screen.paint(
        f"  FIRST TO {target}" if target else "  ENDLESS",
        fg=SECONDARY,
        bold=True,
    )

    screen.frame(
        [header, you_bar + mid + bot_bar, streak_line + " " * 8 + target_line],
        color=PRIMARY,
        fill=CARD,
    )
    screen.line()


def history_strip(screen, history):
    glyphs = {"W": ("W", NEON_GREEN), "L": ("L", DESTRUCTIVE), "T": ("T", MUTED)}
    cells = []
    for item in history[-16:]:
        glyph, color = glyphs[item]
        cells.append(screen.paint(f"[{glyph}]", fg=color, bold=True))
    row = "  " + (" " if not cells else "".join(cells))
    screen.frame([row], color=BORDER, fill=CARD)
    screen.line()


def duel(screen, player_move, bot_move):
    """Animate the head-to-head reveal (the one big motion moment)."""
    span = screen.width - 10
    left_w = span // 2
    right_w = span - left_w
    palette = {"rock": NEON_GREEN, "paper": NEON_CYAN, "scissors": ACCENT}
    shuffle = [ORDER[i % 3] for i in range(3)]

    def render(move_you, move_bot, bot_anim=False):
        color_you = palette[move_you]
        color_bot = NEON_MAGENTA
        if bot_anim:
            color_bot = [NEON_CYAN, NEON_MAGENTA, NEON_GREEN][random.randrange(3)]

        left = [
            screen.paint(HAND[move_you], fg=color_you, bold=True),
            screen.paint(move_you.upper(), fg=color_you, bold=True),
            screen.paint("PLAYER", fg=MUTED),
        ]
        known = "" if bot_anim else move_bot.upper()
        right = [
            screen.paint(HAND[move_bot], fg=color_bot, bold=True),
            screen.paint(known or "???", fg=color_bot, bold=True),
            screen.paint("OPPONENT", fg=MUTED),
        ]
        right = right[::-1]

        rows = []
        for i in range(3):
            vs = "VS" if i == 1 else ""
            rows.append(
                _pad(left[i], left_w, "center")
                + _pad(screen.paint(vs, fg=AMBER, bold=True), 6, "center")
                + _pad(right[i], right_w, "center")
            )
        screen.frame(rows, color=BORDER, fill=CARD)

    screen.title_bar(" DUEL ", color=PRIMARY)
    screen.line()

    if screen.motion:
        for i, move in enumerate(shuffle):
            render(player_move, move, bot_anim=True)
            screen.write("\x1b[6A\x1b[2K")
            time.sleep(0.09 + i * 0.03)
        for i in range(6):
            render(player_move, random.choice(ORDER), bot_anim=True)
            screen.write("\x1b[6A\x1b[2K")
            time.sleep(0.05)
        screen.hide_cursor()
        render(player_move, bot_move)
        screen.show_cursor()
    else:
        render(player_move, bot_move)
    screen.line()


def verdict(screen, outcome, player_move, bot_move):
    """Result banner with sparkles on a win and a shake on a loss."""
    labels = {"win": "YOU WIN", "lose": "YOU LOSE", "tie": "DRAW"}
    colors = {"win": NEON_GREEN, "lose": DESTRUCTIVE, "tie": MUTED}
    color = colors[outcome]

    rows = [
        _pad(screen.paint(row, fg=color, bold=True), screen.width - 4, "center")
        for row in big_text(labels[outcome])
    ]

    if outcome == "win":
        spark_line = "  " + " ".join(
            screen.paint(random.choice(SPARK), fg=random.choice([NEON_CYAN, NEON_GREEN, AMBER, SECONDARY]), bold=True)
            for _ in range((screen.width - 4) // 3)
        )
        rows.append(spark_line)
    elif outcome == "lose":
        rows.append(
            _pad(
                screen.paint(
                    f"  {bot_move.upper()} BEATS {player_move.upper()}",
                    fg=DESTRUCTIVE,
                    bold=True,
                ),
                screen.width - 4,
                "center",
            )
        )
    else:
        rows.append(
            _pad(
                screen.paint(f"  BOTH CHOSE {player_move.upper()}", fg=MUTED),
                screen.width - 4,
                "center",
            )
        )

    if screen.motion and outcome != "win":
        height = len(rows) + 2
        for offset in (2, -2, 1, -1, 0):
            sys.stdout.write("\x1b[%dA" % height)
            screen.write("\r" if offset <= 0 else "\x1b[%dC" % offset)
            screen.frame(rows, color=color, fill=CARD)
            sys.stdout.flush()
            time.sleep(0.05)
    else:
        screen.frame(rows, color=color, fill=CARD)

    screen.bell(tone=(880, 140) if outcome == "win" else (220, 180) if outcome == "lose" else None)
    screen.line()


def report(screen, state, target, aborted=False):
    rounds = state["rounds"] or 1
    rate = state["player"] / rounds * 100
    won = state["player"] > state["computer"]

    if aborted:
        headline = "ABORTED"
    elif state["rounds"]:
        headline = "MATCH OVER"
    else:
        headline = "NO ROUNDS"
    rows = big_text(headline)
    width = screen.width - 4
    rows = [
        _pad(screen.paint(r, fg=ACCENT if won else SECONDARY, bold=True), width, "center")
        for r in rows
    ]
    rows.append("")
    rows.append(
        _pad(
            screen.paint(
                f"YOU {state['player']} : {state['computer']} CPU",
                fg=NEON_GREEN if won else DESTRUCTIVE,
                bold=True,
            ),
            width,
            "center",
        )
    )
    rows.append(
        _pad(
            screen.paint(
                f"WIN RATE {rate:.0f}%   BEST STREAK {state['best']}"
                + (f"   TARGET {target}" if target else "   ENDLESS"),
                fg=MUTED,
            ),
            width,
            "center",
        )
    )
    screen.frame(rows, color=ACCENT if won else BORDER, fill=CARD)
    screen.line()


# --------------------------------------------------------------------------
# game flow
# --------------------------------------------------------------------------


def read_choice(screen):
    """Numeric selection: 1 rock, 2 paper, 3 scissors, 0 to quit."""
    while True:
        prompt = screen.paint("  [1] ROCK", fg=NEON_GREEN, bold=True)
        prompt += screen.paint("   [2] PAPER", fg=NEON_CYAN, bold=True)
        prompt += screen.paint("   [3] SCISSORS", fg=ACCENT, bold=True)
        prompt += screen.paint("   [0] QUIT", fg=MUTED) + screen.paint(" > ", fg=FG)
        raw = input(prompt).strip()

        if raw in NUMBERS:
            return NUMBERS[raw]
        if raw in ("0", "q", "quit", "exit"):
            return None
        if raw and raw[0].upper() in ("R", "P", "S"):
            return {"R": "rock", "P": "paper", "S": "scissors"}[raw[0].upper()]
        screen.line(screen.paint("  INVALID INPUT - ENTER 1, 2, 3 OR 0", fg=DESTRUCTIVE, bold=True))
        screen.line()


def read_target(screen):
    while True:
        raw = input(
            screen.paint("  FIRST TO (odd number, or 0 for endless) > ", fg=SECONDARY)
        ).strip()
        if raw == "0":
            return None
        try:
            value = int(raw)
        except ValueError:
            value = -1
        if value > 0 and value % 2 == 1:
            return value
        screen.line(screen.paint("  ENTER A POSITIVE ODD NUMBER OR 0", fg=DESTRUCTIVE, bold=True))
        screen.line()


def play_match(screen, state, target):
    history = []
    while True:
        hud(screen, state, target)
        cards_screen(screen, cursor=None)
        if history:
            history_strip(screen, history)
        screen.line()

        player = read_choice(screen)
        if player is None:
            return history, True

        bot = random.choice(ORDER)
        duel(screen, player, bot)

        if player == bot:
            outcome = "tie"
        elif BEATS[player] == bot:
            outcome = "win"
        else:
            outcome = "lose"

        verdict(screen, outcome, player, bot)

        state["rounds"] += 1
        if outcome == "win":
            state["player"] += 1
            state["streak"] += 1
        elif outcome == "lose":
            state["computer"] += 1
            state["streak"] = 0
        else:
            state["streak"] = 0
        state["best"] = max(state["best"], state["streak"])
        state["last"] = player
        history.append({"win": "W", "lose": "L", "tie": "T"}[outcome])

        if target and max(state["player"], state["computer"]) >= target:
            return history, False
        screen.sleep(0.5)


def ask_rematch(screen):
    raw = input(
        screen.paint("  [1] REMATCH", fg=NEON_GREEN, bold=True)
        + screen.paint("   [2] EXIT", fg=MUTED)
        + screen.paint(" > ", fg=FG)
    ).strip()
    return raw == "1"


def main():
    plain = "--plain" in sys.argv
    screen = Screen(
        plain=plain,
        no_motion="--no-motion" in sys.argv,
        mute="--mute" in sys.argv,
    )

    if screen.color:
        screen.write("\x1b]0;Rock Paper Scissors\x07")
        boot(screen)

    state = {"player": 0, "computer": 0, "rounds": 0, "streak": 0, "best": 0, "last": "rock"}
    try:
        while True:
            screen.clear()
            for row in logo(screen):
                screen.line(row)
            screen.line()
            screen.line(
                screen.paint("  [1] ROCK", fg=NEON_GREEN, bold=True)
                + screen.paint("   [2] PAPER", fg=NEON_CYAN, bold=True)
                + screen.paint("   [3] SCISSORS", fg=ACCENT, bold=True)
            )
            screen.line()
            target = read_target(screen)

            history, aborted = play_match(screen, state, target)
            if history:
                history_strip(screen, history)
            report(screen, state, target, aborted=aborted)
            if not ask_rematch(screen):
                break
            state = {"player": 0, "computer": 0, "rounds": 0, "streak": 0, "best": 0, "last": "rock"}
    except (KeyboardInterrupt, EOFError):
        screen.line()
        screen.line(screen.paint("  CONNECTION SEVERED", fg=ACCENT, bold=True))
    finally:
        screen.show_cursor()
        if screen.color:
            sys.stdout.write("\x1b[0m")


if __name__ == "__main__":
    main()