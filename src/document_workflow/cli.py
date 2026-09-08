"""Command line interface for document workflow automation."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from .core import RulesError, load_rules
from .workflow import process_documents


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="document-workflow",
        description="Classify and copy text-like documents into category folders.",
    )
    parser.add_argument("input", type=Path, help="Directory to scan recursively")
    parser.add_argument("--output", required=True, type=Path, help="Destination directory")
    parser.add_argument("--rules", required=True, type=Path, help="Keyword rules JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Plan without writing files")
    return parser


def _validate_paths(input_dir: Path, output_dir: Path) -> None:
    resolved_input = input_dir.resolve()
    resolved_output = output_dir.resolve()
    if not resolved_input.is_dir():
        raise ValueError(f"Input directory does not exist: {input_dir}")
    if resolved_output == resolved_input or resolved_output.is_relative_to(resolved_input):
        raise ValueError("Output directory must be outside the input directory")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        _validate_paths(args.input, args.output)
        rules = load_rules(args.rules)
        summary = process_documents(args.input, args.output, rules, dry_run=args.dry_run)
    except (OSError, RulesError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    payload = {
        "summary": {
            "copied": summary.copied,
            "skipped": summary.skipped,
            "errors": summary.errors,
        },
        "records": [asdict(record) for record in summary.records],
        "dry_run": args.dry_run,
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 1 if summary.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
