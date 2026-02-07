from typing import Any, Iterable, List

from registry import CheckResult, Status, register_check


def _normalize_schema(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    return []


@register_check(name="schema", description="Schema matches expected fields.")
def check_schema(dataset: Any, now: Any) -> CheckResult:
    actual = _normalize_schema(dataset.get("schema"))
    expected = _normalize_schema(dataset.get("expected_schema"))

    if not actual or not expected:
        return CheckResult(
            name="schema",
            status=Status.YELLOW,
            message="Missing schema or expected_schema metadata.",
            details={"schema": actual, "expected_schema": expected},
        )

    actual_set = set(actual)
    expected_set = set(expected)
    missing = sorted(expected_set - actual_set)
    extra = sorted(actual_set - expected_set)

    if missing:
        status = Status.RED
        message = "Missing expected fields."
    elif extra:
        status = Status.YELLOW
        message = "Schema has extra fields."
    else:
        status = Status.GREEN
        message = "Schema matches expected fields."

    return CheckResult(
        name="schema",
        status=status,
        message=message,
        details={"missing": missing, "extra": extra},
    )
