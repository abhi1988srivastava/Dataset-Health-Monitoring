from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from explain import render_html
from health import evaluate_all
from registry import (
    CHECK_REGISTRY,
    DatasetRegistry,
    load_builtin_checks,
    load_entrypoint_checks,
    parse_datetime,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate dataset health reports.")
    parser.add_argument(
        "--datasets",
        default="datasets",
        help="Path to dataset YAML file or directory (default: datasets).",
    )
    parser.add_argument("--out-json", default="health.json", help="JSON output path.")
    parser.add_argument("--out-html", default="health.html", help="HTML output path.")
    parser.add_argument("--no-json", action="store_true", help="Disable JSON output.")
    parser.add_argument("--no-html", action="store_true", help="Disable HTML output.")
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print JSON report to stdout.",
    )
    parser.add_argument(
        "--now",
        default=None,
        help="Override current time (ISO 8601) for deterministic runs.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    dataset_path = Path(args.datasets)

    registry = DatasetRegistry()
    registry.load_from_path(dataset_path)

    load_builtin_checks()
    _, errors = load_entrypoint_checks()
    if errors:
        for error in errors:
            print(f"Plugin warning: {error}", file=sys.stderr)

    now = parse_datetime(args.now) if args.now else None
    report = evaluate_all(registry.list(), CHECK_REGISTRY, now=now)
    report_payload = report.to_dict()

    if args.stdout:
        print(json.dumps(report_payload, indent=2, ensure_ascii=True, sort_keys=True))

    if not args.no_json:
        json_path = Path(args.out_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(report_payload, indent=2, ensure_ascii=True, sort_keys=True)
        )

    if not args.no_html:
        html_path = Path(args.out_html)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(render_html(report))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
