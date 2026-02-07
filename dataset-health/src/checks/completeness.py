from typing import Any

from registry import CheckResult, Status, register_check


@register_check(name="completeness", description="Dataset meets expected record count.")
def check_completeness(dataset: Any, now: Any) -> CheckResult:
    record_count = dataset.get("record_count")
    expected_min = dataset.get("expected_min_records")

    if record_count is None or expected_min is None:
        return CheckResult(
            name="completeness",
            status=Status.YELLOW,
            message="Missing record_count or expected_min_records metadata.",
            details={"record_count": record_count, "expected_min_records": expected_min},
        )

    try:
        record_count_value = float(record_count)
        expected_min_value = float(expected_min)
    except (TypeError, ValueError):
        return CheckResult(
            name="completeness",
            status=Status.YELLOW,
            message="Invalid record_count or expected_min_records value.",
            details={"record_count": record_count, "expected_min_records": expected_min},
        )

    if expected_min_value <= 0:
        return CheckResult(
            name="completeness",
            status=Status.YELLOW,
            message="expected_min_records must be greater than 0.",
            details={"expected_min_records": expected_min_value},
        )

    ratio = record_count_value / expected_min_value
    if record_count_value >= expected_min_value:
        status = Status.GREEN
        message = "Record count meets expected minimum."
    elif ratio >= 0.9:
        status = Status.YELLOW
        message = "Record count slightly below expected minimum."
    else:
        status = Status.RED
        message = "Record count significantly below expected minimum."

    return CheckResult(
        name="completeness",
        status=status,
        message=message,
        details={
            "record_count": record_count_value,
            "expected_min_records": expected_min_value,
            "ratio": round(ratio, 3),
        },
    )
