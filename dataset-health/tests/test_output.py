from __future__ import annotations

from datetime import datetime, timezone
import json

from health import DatasetHealth, HealthReport
from output import (
    build_cloudwatch_metrics,
    overall_status,
    parse_cloudwatch_dimensions,
    render_jsonl,
    render_prometheus,
    render_summary_json,
    status_value,
)
from registry import CheckResult, Dataset, Status


def _report() -> HealthReport:
    checks_green = [CheckResult(name="check", status=Status.GREEN, message="ok")]
    checks_red = [CheckResult(name="check", status=Status.RED, message="bad")]
    return HealthReport(
        generated_at=datetime(2026, 2, 7, tzinfo=timezone.utc),
        datasets=[
            DatasetHealth(
                dataset=Dataset(name="alpha", owner="team-a"),
                status=Status.GREEN,
                checks=checks_green,
            ),
            DatasetHealth(
                dataset=Dataset(name="beta", owner="team-b"),
                status=Status.RED,
                checks=checks_red,
            ),
        ],
    )


def test_summary_json() -> None:
    report = _report()
    payload = render_summary_json(report)

    assert payload["status"] == "RED"
    assert payload["counts"]["GREEN"] == 1
    assert payload["counts"]["RED"] == 1
    assert payload["counts"]["YELLOW"] == 0
    assert payload["counts"]["total"] == 2


def test_jsonl_output() -> None:
    report = _report()
    lines = render_jsonl(report).splitlines()
    assert len(lines) == 2
    payloads = [json.loads(line) for line in lines]
    assert {item["dataset"] for item in payloads} == {"alpha", "beta"}


def test_prometheus_output() -> None:
    report = _report()
    output = render_prometheus(report)
    assert "dataset_health_status" in output
    assert 'dataset_health_dataset_status{dataset="alpha"}' in output
    assert 'dataset_health_dataset_status{dataset="beta"}' in output


def test_cloudwatch_dimensions_parsing() -> None:
    dims = parse_cloudwatch_dimensions("env=prod,team=data-platform")
    assert dims == [
        {"Name": "env", "Value": "prod"},
        {"Name": "team", "Value": "data-platform"},
    ]


def test_build_cloudwatch_metrics() -> None:
    report = _report()
    metrics = build_cloudwatch_metrics(report, base_dimensions=[], include_datasets=True)
    assert len(metrics) == 7
    names = {metric["MetricName"] for metric in metrics}
    assert "DatasetHealthOverallStatus" in names
    assert "DatasetHealthCount" in names
    assert "DatasetHealthTotal" in names
    assert "DatasetHealthDatasetStatus" in names


def test_overall_status_and_value() -> None:
    report = _report()
    assert overall_status(report) == Status.RED
    assert status_value(Status.GREEN) == 0
    assert status_value(Status.YELLOW) == 1
    assert status_value(Status.RED) == 2
