"""Command-line entry point for the Silicon Signal Triage showcase."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from eda_hpc_triage.parser import parse_log_file
from eda_hpc_triage.render import format_report
from eda_hpc_triage.scheduler import DEFAULT_WORKERS, build_report, load_workers


def main(argv: list[str] | None = None) -> int:
    """Run the showcase CLI."""

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "triage":
        workers = load_workers(args.workers) if args.workers else DEFAULT_WORKERS
        records, ignored = parse_log_file(args.logfile)
        report = build_report(records, ignored_lines=len(ignored), workers=workers)

        if args.json:
            print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
        else:
            print(format_report(report))
        return 0

    parser.print_help()
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="silicon-signal-triage",
        description=(
            "Classify EDA regression failures and assign them to a distributed "
            "CEC-style support cluster."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    triage = subparsers.add_parser("triage", help="triage an EDA regression log")
    triage.add_argument("logfile", type=Path, help="path to structured EDA log")
    triage.add_argument(
        "--workers",
        type=Path,
        help="optional JSON worker topology",
    )
    triage.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of text",
    )

    return parser


if __name__ == "__main__":
    raise SystemExit(main())
