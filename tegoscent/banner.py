"""
banner.py - the TegoScent startup banner and quick-start guide.

Prints a neon, cyberpunk-styled ASCII logo (gradient colored via 24-bit ANSI
escapes) followed, on --help / no-args invocations, by a "replace the
placeholders with your target" command cheat-sheet.

Colour is skipped automatically when stdout isn't a terminal or when NO_COLOR
/ TEGOSCENT_NO_COLOR is set (https://no-color.org convention). The whole
banner can be turned off with --no-banner or TEGOSCENT_NO_BANNER=1, which is
useful when piping tegoscent's stdout into another tool.
"""

from __future__ import annotations
import os
import sys
from typing import List, Tuple

RGB = Tuple[int, int, int]

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"

# The "big" figlet font, generated for "TEGOSCENT" - kept as a raw block so
# the gradient function below can walk it line by line.
LOGO_LINES: List[str] = [
    r" _______ ______ _____  ____   _____  _____ ______ _   _ _______ ",
    r"|__   __|  ____/ ____|/ __ \ / ____|/ ____|  ____| \ | |__   __|",
    r"   | |  | |__ | |  __| |  | | (___ | |    | |__  |  \| |  | |   ",
    r"   | |  |  __|| | |_ | |  | |\___ \| |    |  __| | . ` |  | |   ",
    r"   | |  | |___| |__| | |__| |____) | |____| |____| |\  |  | |   ",
    r"   |_|  |______\_____|\____/|_____/ \_____|______|_| \_|  |_|   ",
]
LOGO_WIDTH = max(len(line) for line in LOGO_LINES)

# Neon cyberpunk gradient stops: electric cyan -> violet -> hot magenta/pink.
GRADIENT_STOPS: List[RGB] = [
    (0, 255, 255),    # electric cyan
    (0, 200, 255),    # cyan-blue
    (140, 60, 255),   # electric violet
    (255, 0, 220),    # magenta
    (255, 20, 147),   # hot pink
]

ACCENT = (57, 255, 20)     # acid green - used for the tagline/prompt accent
MUTED = (110, 110, 130)    # dim slate - used for rule lines / secondary text


def _lerp(a: RGB, b: RGB, t: float) -> RGB:
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))  # type: ignore[return-value]


def _multi_gradient(stops: List[RGB], t: float) -> RGB:
    t = max(0.0, min(1.0, t))
    segments = len(stops) - 1
    pos = t * segments
    i = min(int(pos), segments - 1)
    return _lerp(stops[i], stops[i + 1], pos - i)


def _fg(rgb: RGB) -> str:
    r, g, b = rgb
    return f"\x1b[38;2;{r};{g};{b}m"


def supports_color() -> bool:
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("TEGOSCENT_NO_COLOR") is not None:
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def banner_enabled(argv: List[str]) -> bool:
    if os.environ.get("TEGOSCENT_NO_BANNER") is not None:
        return False
    return "--no-banner" not in argv


def render_logo(color: bool = True) -> str:
    lines = []
    n = len(LOGO_LINES)
    for i, text in enumerate(LOGO_LINES):
        if not color:
            lines.append(text)
            continue
        rgb = _multi_gradient(GRADIENT_STOPS, i / max(1, n - 1))
        lines.append(f"{BOLD}{_fg(rgb)}{text}{RESET}")
    return "\n".join(lines)


def render_tagline(color: bool = True) -> str:
    rule = "\u2500" * LOGO_WIDTH  # ─
    title = "FREE & OPEN-SOURCE OSINT LINK-ANALYSIS ENGINE".center(LOGO_WIDTH)
    prompt = "root@tegoscent:~# initiate_recon --target ???".center(LOGO_WIDTH)

    if not color:
        return f"{rule}\n{title}\n{prompt}\n{rule}"

    return (
        f"{_fg(MUTED)}{rule}{RESET}\n"
        f"{BOLD}{_fg(GRADIENT_STOPS[-1])}{title}{RESET}\n"
        f"{DIM}{_fg(ACCENT)}{prompt}{RESET}\n"
        f"{_fg(MUTED)}{rule}{RESET}"
    )


def render_guide(color: bool = True) -> str:
    def head(text: str) -> str:
        return f"{BOLD}{_fg(ACCENT)}{text}{RESET}" if color else text

    def cmd(text: str) -> str:
        return f"{_fg(GRADIENT_STOPS[1])}{text}{RESET}" if color else text

    def ph(text: str) -> str:
        # placeholders rendered in hot pink so they visually scream "replace me"
        return f"{BOLD}{_fg(GRADIENT_STOPS[-1])}{text}{RESET}" if color else text

    def dim(text: str) -> str:
        return f"{DIM}{_fg(MUTED)}{text}{RESET}" if color else text

    lines = [
        "",
        head("QUICK START"),
        "",
        "  SYNTAX:",
        f"    {cmd('tegoscent run')} {ph('<ENTITY_TYPE>')} {ph('<TARGET_VALUE>')} {dim('[OPTIONS]')}",
        "",
        f"  {ph('<ENTITY_TYPE>')} is one of: Domain, IPv4Address, EmailAddress, Username,",
        "  PhoneNumber, Person, Organization, URL, ...  " + dim("(full list: tegoscent list-entities)"),
        "",
        head("EXAMPLES") + dim("  -  replace every <...> placeholder with your real target"),
        "",
        f"    {cmd('tegoscent run Domain')} {ph('<target-domain.com>')} --machine footprint_l2 --depth 2 -o report.html",
        f"    {cmd('tegoscent run EmailAddress')} {ph('<target@example.com>')} --machine person_footprint",
        f"    {cmd('tegoscent run Username')} {ph('<target_handle>')} --depth 1",
        f"    {cmd('tegoscent run IPv4Address')} {ph('<1.2.3.4>')} --machine footprint_l2 --format json -o report.json",
        f"    {cmd('tegoscent run PhoneNumber')} {ph('<+15551234567>')} --machine person_footprint",
        "",
        head("USEFUL COMMANDS"),
        "",
        f"    {cmd('tegoscent list-entities')}      list every supported entity type",
        f"    {cmd('tegoscent list-transforms')}    list every transform, grouped by input type",
        f"    {cmd('tegoscent list-machines')}      list named transform chains (\"machines\")",
        "",
        head("COMMON FLAGS"),
        "",
        f"    --machine {ph('<name>')}      run a named transform chain " + dim("(footprint_l1, footprint_l2, person_footprint, full_recon)"),
        f"    --depth {ph('<N>')}           transform hops from the seed  " + dim("(default: 2)"),
        f"    --format {ph('<fmt>')}        html | json | graphml | csv  " + dim("(default: inferred from -o)"),
        f"    -o, --output {ph('<path>')}   where to write the result    " + dim("(default: tegoscent_output.html)"),
        "    -v, --verbose         debug logging",
        "    --no-banner           suppress this banner  " + dim("(or set TEGOSCENT_NO_BANNER=1)"),
        "",
        dim("  Full reference: tegoscent --help"),
        "",
    ]
    return "\n".join(lines)


def print_banner(show_guide: bool = False, color: bool | None = None) -> None:
    if color is None:
        color = supports_color()
    print(render_logo(color))
    print(render_tagline(color))
    if show_guide:
        print(render_guide(color))
