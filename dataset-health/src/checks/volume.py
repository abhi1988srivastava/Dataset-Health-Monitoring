from typing import Any

from registry import CheckResult, Status, register_check


def _format_bytes(value: float) -> str:
    thresholds = [
        (1024 ** 4, "TB"),
        (1024 ** 3, "GB"),
        (1024 ** 2, "MB"),
        (1024, "KB"),
    ]
    for factor, unit in thresholds:
        if value >= factor:
            return f"{value / factor:.2f} {unit}"
    return f"{value:.0f} B"


@register_check(name="volume", description="Dataset volume meets expected minimum.")
def check_volume(dataset: Any, now: Any) -> CheckResult:
    size_bytes = dataset.get("bytes")
    expected_min = dataset.get("expected_min_bytes")

    if size_bytes is None or expected_min is None:
        return CheckResult(
            name="volume",
            status=Status.YELLOW,
            message="Missing bytes or expected_min_bytes metadata.",
            details={"bytes": size_bytes, "expected_min_bytes": expected_min},
        )

    try:
        size_value = float(size_bytes)
        expected_min_value = float(expected_min)
    except (TypeError, ValueError):
        return CheckResult(
            name="volume",
            status=Status.YELLOW,
            message="Invalid bytes or expected_min_bytes value.",
            details={"bytes": size_bytes, "expected_min_bytes": expected_min},
        )

    if expected_min_value <= 0:
        return CheckResult(
            name="volume",
            status=Status.YELLOW,
            message="expected_min_bytes must be greater than 0.",
            details={"expected_min_bytes": expected_min_value},
        )

    ratio = size_value / expected_min_value
    if size_value >= expected_min_value:
        status = Status.GREEN
        message = "Volume meets expected minimum."
    elif ratio >= 0.9:
        status = Status.YELLOW
        message = "Volume slightly below expected minimum."
    else:
        status = Status.RED
        message = "Volume significantly below expected minimum."

    return CheckResult(
        name="volume",
        status=status,
        message=message,
        details={
            "bytes": size_value,
            "expected_min_bytes": expected_min_value,
            "ratio": round(ratio, 3),
            "bytes_human": _format_bytes(size_value),
            "expected_min_human": _format_bytes(expected_min_value),
        },
    )
