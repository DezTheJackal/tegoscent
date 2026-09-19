#!/usr/bin/env python3
"""
tegoscent/cli.py - TegoScent: free, open-source link-analysis / OSINT tool.

Usage examples:
    tegoscent run Domain example.com --depth 2 --output out.html
    tegoscent run Domain example.com --machine footprint_l2 --format json --output out.json
    tegoscent run EmailAddress user@example.com --machine person_footprint
    tegoscent run Username someuser --depth 1
    tegoscent list-transforms
    tegoscent list-machines

Requirements (pip install -r requirements.txt):
    requests, dnspython, python-whois, networkx, pyvis, ipwhois, phonenumbers, shodan
"""

from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path

from . import transforms  # noqa: F401  (import registers all built-in transforms)
from .config import load_config
from .engine import Engine, MACHINES
from .entities import ENTITY_TYPES, make_entity
from .graph import TegoGraph
from .transforms.base import all_transforms
from .visualize import render_html


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tegoscent",
        description="TegoScent - free, open-source Maltego-style link-analysis / OSINT tool.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging.")
    parser.add_argument("--config", default=None, help="Path to JSON config file (default: ~/.tegoscent.json).")
    parser.add_argument("--timeout", type=int, default=10, help="Per-transform network timeout, seconds (default: 10).")

    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Run transforms starting from a seed entity.")
    p_run.add_argument("entity_type", choices=sorted(ENTITY_TYPES), help="Seed entity type.")
    p_run.add_argument("value", help="Seed entity value, e.g. example.com, 1.2.3.4, user@example.com")
    p_run.add_argument("--depth", type=int, default=2, help="Max transform hops from the seed (default: 2).")
    p_run.add_argument("--machine", choices=sorted(MACHINES), default=None,
                        help="Run a named transform chain instead of every applicable transform.")
    p_run.add_argument("--transforms", nargs="*", default=None,
                        help="Explicit whitelist of transform names to run (overrides --machine).")
    p_run.add_argument("--output", "-o", default="tegoscent_output.html",
                        help="Output file path (default: tegoscent_output.html).")
    p_run.add_argument("--format", choices=["html", "json", "graphml", "csv"], default=None,
                        help="Output format. Defaults to extension of --output.")
    p_run.add_argument("--max-workers", type=int, default=8, help="Concurrent transform workers (default: 8).")

    sub.add_parser("list-transforms", help="List every registered transform, grouped by input entity type.")
    sub.add_parser("list-machines", help="List named transform chains ('machines').")
    sub.add_parser("list-entities", help="List every supported entity type.")

    return parser


def cmd_list_transforms() -> None:
    for input_type, entries in sorted(all_transforms().items()):
        print(f"\n{input_type}")
        for t in entries:
            print(f"  - {t['name']:<32} {t['description']}")


def cmd_list_machines() -> None:
    for name, whitelist in sorted(MACHINES.items()):
        scope = "ALL registered transforms" if not whitelist else ", ".join(whitelist)
        print(f"{name}\n    {scope}\n")


def cmd_list_entities() -> None:
    for name in sorted(ENTITY_TYPES):
        print(name)


def infer_format(output_path: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    ext = Path(output_path).suffix.lower().lstrip(".")
    return {"html": "html", "json": "json", "graphml": "graphml", "csv": "csv"}.get(ext, "html")


def cmd_run(args: argparse.Namespace, config: dict) -> int:
    try:
        seed = make_entity(args.entity_type, args.value)
    except ValueError as exc:
        print(f"[!] {exc}", file=sys.stderr)
        return 2

    allowed = args.transforms
    if not allowed and args.machine:
        allowed = MACHINES[args.machine] or None  # empty list -> None -> run everything

    graph = TegoGraph()
    engine = Engine(graph, config, max_workers=args.max_workers)

    print(f"[*] Seeding graph with {seed}")
    engine.run([seed], depth=args.depth, allowed_transforms=allowed)
    print(f"[+] Done: {graph.node_count()} entities, {graph.edge_count()} links")

    fmt = infer_format(args.output, args.format)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)  # cross-platform mkdir -p; no-op if parent is "."

    try:
        if fmt == "html":
            render_html(graph, args.output, title=f"TegoScent - {seed.value}")
        elif fmt == "json":
            graph.save_json(args.output)
        elif fmt == "graphml":
            graph.save_graphml(args.output)
        elif fmt == "csv":
            graph.save_csv_edgelist(args.output)
    except Exception as exc:
        print(f"[!] Failed writing output ({fmt}): {exc}", file=sys.stderr)
        return 1

    print(f"[+] Wrote {fmt.upper()} output to {args.output}")
    return 0


def _harden_console_encoding() -> None:
    """
    Windows cmd.exe / PowerShell can still default to a legacy codepage
    (cp1252/cp437) rather than UTF-8, which raises UnicodeEncodeError on
    anything outside ASCII (accented domain names, IDN labels, etc.).
    reconfigure() is available on Python 3.7+ text streams on every OS;
    guard it anyway in case stdout has been replaced with something that
    doesn't support it (e.g. some CI runners / redirected pipes).
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    _harden_console_encoding()
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if args.command == "list-transforms":
        cmd_list_transforms()
        return 0
    if args.command == "list-machines":
        cmd_list_machines()
        return 0
    if args.command == "list-entities":
        cmd_list_entities()
        return 0

    config = load_config(args.config, timeout=args.timeout)

    if args.command == "run":
        try:
            return cmd_run(args, config)
        except KeyboardInterrupt:
            print("\n[!] Interrupted.", file=sys.stderr)
            return 130

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
