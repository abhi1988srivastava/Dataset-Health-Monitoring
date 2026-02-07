from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from explain import render_html
from health import evaluate_all
from output import (
    emit_cloudwatch_metrics,
    overall_status,
    parse_cloudwatch_dimensions,
    render_jsonl,
    render_prometheus,
    render_summary_json,
)
from registry import (
    CHECK_REGISTRY,
    DatasetRegistry,
    load_builtin_checks,
    load_entrypoint_checks,
    parse_datetime,
    Status,
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
        "--output",
        choices=["report-json", "summary-json", "jsonl", "prometheus", "cloudwatch"],
        default=None,
        help="Single output format for automation workflows.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output file path for --output modes (defaults to stdout).",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print JSON report to stdout.",
    )
    parser.add_argument(
        "--fail-on",
        choices=["none", "yellow", "red"],
        default="none",
        help="Exit non-zero if the overall status meets or exceeds the threshold.",
    )
    parser.add_argument(
        "--cloudwatch-namespace",
        default="DatasetHealth",
        help="CloudWatch namespace for metrics output.",
    )
    parser.add_argument(
        "--cloudwatch-region",
        default=None,
        help="AWS region for CloudWatch metrics (defaults to AWS SDK config).",
    )
    parser.add_argument(
        "--cloudwatch-dimensions",
        default="",
        help="Comma-separated CloudWatch dimensions (key=value,key2=value2).",
    )
    parser.add_argument(
        "--cloudwatch-no-datasets",
        action="store_true",
        help="Disable per-dataset CloudWatch metrics.",
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
    overall = overall_status(report)

    if args.output:
        if args.output == "report-json":
            output_text = json.dumps(
                report_payload, indent=2, ensure_ascii=True, sort_keys=True
            )
        elif args.output == "summary-json":
            output_text = json.dumps(
                render_summary_json(report),
                indent=2,
                ensure_ascii=True,
                sort_keys=True,
            )
        elif args.output == "jsonl":
            output_text = render_jsonl(report)
        elif args.output == "prometheus":
            output_text = render_prometheus(report)
        elif args.output == "cloudwatch":
            try:
                dimensions = parse_cloudwatch_dimensions(args.cloudwatch_dimensions)
                emit_cloudwatch_metrics(
                    report,
                    namespace=args.cloudwatch_namespace,
                    base_dimensions=dimensions,
                    region=args.cloudwatch_region,
                    include_datasets=not args.cloudwatch_no_datasets,
                )
            except Exception as exc:
                print(f"CloudWatch output failed: {exc}", file=sys.stderr)
                return 1
            output_text = None
        else:  # pragma: no cover - guarded by argparse choices
            output_text = None

        if output_text is not None:
            if args.stdout or not args.out:
                print(output_text)
            else:
                out_path = Path(args.out)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(output_text)
    else:
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

    if args.fail_on == "red" and overall == Status.RED:
        return 2
    if args.fail_on == "yellow" and overall in (Status.YELLOW, Status.RED):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
