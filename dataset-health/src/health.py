from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List

from registry import CheckRegistry, CheckResult, Dataset, Status


def aggregate_status(results: Iterable[CheckResult]) -> Status:
    statuses = {result.status for result in results}
    if Status.RED in statuses:
        return Status.RED
    if Status.YELLOW in statuses:
        return Status.YELLOW
    return Status.GREEN


@dataclass(frozen=True)
class DatasetHealth:
    dataset: Dataset
    status: Status
    checks: List[CheckResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "dataset": self.dataset.to_dict(),
            "status": self.status.value,
            "checks": [check.to_dict() for check in self.checks],
        }


@dataclass(frozen=True)
class HealthReport:
    generated_at: datetime
    datasets: List[DatasetHealth]

    def summary(self) -> Dict[str, int]:
        counts = {status.value: 0 for status in Status}
        for dataset in self.datasets:
            counts[dataset.status.value] += 1
        counts["total"] = len(self.datasets)
        return counts

    def to_dict(self) -> Dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "summary": self.summary(),
            "datasets": [dataset.to_dict() for dataset in self.datasets],
        }


def evaluate_dataset(dataset: Dataset, registry: CheckRegistry, now: datetime) -> DatasetHealth:
    check_results = registry.run_all(dataset, now)
    status = aggregate_status(check_results)
    return DatasetHealth(dataset=dataset, status=status, checks=check_results)


def evaluate_all(datasets: Iterable[Dataset], registry: CheckRegistry, now: datetime | None = None) -> HealthReport:
    evaluation_time = now or datetime.now(timezone.utc)
    dataset_reports = [
        evaluate_dataset(dataset, registry=registry, now=evaluation_time)
        for dataset in datasets
    ]
    return HealthReport(generated_at=evaluation_time, datasets=dataset_reports)
