from __future__ import annotations

from datetime import datetime, timezone

from checks.completeness import check_completeness
from checks.freshness import check_freshness
from checks.schema import check_schema
from checks.volume import check_volume
from registry import Dataset, Status


NOW = datetime(2026, 2, 7, 18, 30, 0, tzinfo=timezone.utc)


def _dataset(metadata: dict) -> Dataset:
    return Dataset(name="sample", metadata=metadata)


def test_freshness_green() -> None:
    dataset = _dataset(
        {"last_updated": "2026-02-07T12:30:00Z", "freshness_hours": 12}
    )
    result = check_freshness(dataset, NOW)
    assert result.status == Status.GREEN


def test_freshness_red() -> None:
    dataset = _dataset(
        {"last_updated": "2026-02-05T10:30:00Z", "freshness_hours": 12}
    )
    result = check_freshness(dataset, NOW)
    assert result.status == Status.RED


def test_completeness_thresholds() -> None:
    dataset_green = _dataset({"record_count": 120, "expected_min_records": 100})
    dataset_yellow = _dataset({"record_count": 95, "expected_min_records": 100})
    dataset_red = _dataset({"record_count": 50, "expected_min_records": 100})

    assert check_completeness(dataset_green, NOW).status == Status.GREEN
    assert check_completeness(dataset_yellow, NOW).status == Status.YELLOW
    assert check_completeness(dataset_red, NOW).status == Status.RED


def test_schema_missing_and_extra() -> None:
    dataset_missing = _dataset(
        {"schema": ["id", "user_id"], "expected_schema": ["id", "user_id", "ts"]}
    )
    dataset_extra = _dataset(
        {"schema": ["id", "user_id", "ts", "device"], "expected_schema": ["id", "user_id", "ts"]}
    )
    dataset_match = _dataset(
        {"schema": ["id", "user_id"], "expected_schema": ["id", "user_id"]}
    )

    assert check_schema(dataset_missing, NOW).status == Status.RED
    assert check_schema(dataset_extra, NOW).status == Status.YELLOW
    assert check_schema(dataset_match, NOW).status == Status.GREEN


def test_volume_thresholds() -> None:
    dataset_green = _dataset({"bytes": 1200, "expected_min_bytes": 1000})
    dataset_yellow = _dataset({"bytes": 950, "expected_min_bytes": 1000})
    dataset_red = _dataset({"bytes": 500, "expected_min_bytes": 1000})

    assert check_volume(dataset_green, NOW).status == Status.GREEN
    assert check_volume(dataset_yellow, NOW).status == Status.YELLOW
    assert check_volume(dataset_red, NOW).status == Status.RED
