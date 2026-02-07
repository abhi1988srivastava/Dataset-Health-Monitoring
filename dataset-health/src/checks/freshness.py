from datetime import datetime, timezone
from typing import Any

from registry import CheckResult, Status, register_check, parse_datetime


@register_check(name="freshness", description="Data is updated within freshness SLA.")
def check_freshness(dataset: Any, now: datetime) -> CheckResult:
    now = now or datetime.now(timezone.utc)
    last_updated = parse_datetime(dataset.get("last_updated"))
    freshness_hours = dataset.get("freshness_hours")

    if last_updated is None or freshness_hours is None:
        return CheckResult(
            name="freshness",
            status=Status.YELLOW,
            message="Missing last_updated or freshness_hours metadata.",
            details={"last_updated": dataset.get("last_updated"), "freshness_hours": freshness_hours},
        )

    try:
        sla_hours = float(freshness_hours)
    except (TypeError, ValueError):
        return CheckResult(
            name="freshness",
            status=Status.YELLOW,
            message="Invalid freshness_hours value.",
            details={"freshness_hours": freshness_hours},
        )

    age_hours = (now - last_updated).total_seconds() / 3600
    if age_hours <= sla_hours:
        status = Status.GREEN
    elif age_hours <= sla_hours * 1.5:
        status = Status.YELLOW
    else:
        status = Status.RED

    return CheckResult(
        name="freshness",
        status=status,
        message=f"Age {age_hours:.1f}h (SLA {sla_hours:.1f}h).",
        details={
            "last_updated": last_updated.isoformat(),
            "age_hours": round(age_hours, 2),
            "sla_hours": sla_hours,
        },
    )
