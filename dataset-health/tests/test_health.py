from __future__ import annotations

from datetime import datetime, timezone

from health import aggregate_status, evaluate_all
from registry import CheckRegistry, CheckResult, Dataset, Status


def test_aggregate_status() -> None:
    results = [
        CheckResult(name="a", status=Status.GREEN, message="ok"),
        CheckResult(name="b", status=Status.YELLOW, message="warn"),
    ]
    assert aggregate_status(results) == Status.YELLOW

    results.append(CheckResult(name="c", status=Status.RED, message="bad"))
    assert aggregate_status(results) == Status.RED


def test_evaluate_all_summary() -> None:
    registry = CheckRegistry()

    def runner(dataset: Dataset, now: datetime) -> CheckResult:
        status = Status.RED if dataset.name == "bad" else Status.GREEN
        return CheckResult(name="dummy", status=status, message="ok")

    registry.register("dummy", "test", runner)

    datasets = [Dataset(name="good"), Dataset(name="bad")]
    report = evaluate_all(datasets, registry, now=datetime(2026, 2, 7, tzinfo=timezone.utc))
    summary = report.summary()

    assert summary["GREEN"] == 1
    assert summary["RED"] == 1
    assert summary["YELLOW"] == 0
    assert summary["total"] == 2
