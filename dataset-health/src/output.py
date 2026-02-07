from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Dict, Iterable, List, Optional

from health import HealthReport
from registry import Status


STATUS_TO_VALUE = {
    Status.GREEN: 0,
    Status.YELLOW: 1,
    Status.RED: 2,
}


def overall_status(report: HealthReport) -> Status:
    statuses = {dataset.status for dataset in report.datasets}
    if Status.RED in statuses:
        return Status.RED
    if Status.YELLOW in statuses:
        return Status.YELLOW
    return Status.GREEN


def status_value(status: Status) -> int:
    return STATUS_TO_VALUE[status]


def render_summary_json(report: HealthReport) -> Dict[str, object]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "status": overall_status(report).value,
        "counts": report.summary(),
    }


def render_jsonl(report: HealthReport) -> str:
    lines: List[str] = []
    for dataset_report in report.datasets:
        dataset = dataset_report.dataset
        payload = {
            "dataset": dataset.name,
            "status": dataset_report.status.value,
            "owner": dataset.owner,
            "location": dataset.location,
        }
        lines.append(json.dumps(payload, ensure_ascii=True))
    return "\n".join(lines)


def _prom_label_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def render_prometheus(report: HealthReport) -> str:
    overall = overall_status(report)
    summary = report.summary()
    lines: List[str] = [
        "# HELP dataset_health_status Overall dataset health status (0=GREEN,1=YELLOW,2=RED).",
        "# TYPE dataset_health_status gauge",
        f"dataset_health_status {status_value(overall)}",
        "# HELP dataset_health_summary Dataset counts by status.",
        "# TYPE dataset_health_summary gauge",
        f'dataset_health_summary{{status="GREEN"}} {summary["GREEN"]}',
        f'dataset_health_summary{{status="YELLOW"}} {summary["YELLOW"]}',
        f'dataset_health_summary{{status="RED"}} {summary["RED"]}',
        f'dataset_health_summary{{status="TOTAL"}} {summary["total"]}',
        "# HELP dataset_health_dataset_status Per-dataset health status (0=GREEN,1=YELLOW,2=RED).",
        "# TYPE dataset_health_dataset_status gauge",
    ]
    for dataset_report in report.datasets:
        dataset_name = _prom_label_value(dataset_report.dataset.name)
        lines.append(
            f'dataset_health_dataset_status{{dataset="{dataset_name}"}} {status_value(dataset_report.status)}'
        )
    return "\n".join(lines)


def parse_cloudwatch_dimensions(raw: str) -> List[Dict[str, str]]:
    if not raw:
        return []
    dimensions: List[Dict[str, str]] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError("CloudWatch dimensions must be key=value pairs")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            raise ValueError("CloudWatch dimensions must be key=value pairs")
        dimensions.append({"Name": key, "Value": value})
    return dimensions


def build_cloudwatch_metrics(
    report: HealthReport,
    base_dimensions: List[Dict[str, str]],
    include_datasets: bool = True,
) -> List[Dict[str, object]]:
    if len(base_dimensions) > 9:
        raise ValueError("CloudWatch dimensions limit exceeded (max 9 base dimensions).")
    summary = report.summary()
    metrics: List[Dict[str, object]] = [
        {
            "MetricName": "DatasetHealthOverallStatus",
            "Dimensions": base_dimensions,
            "Value": status_value(overall_status(report)),
            "Unit": "None",
        },
        {
            "MetricName": "DatasetHealthTotal",
            "Dimensions": base_dimensions,
            "Value": summary["total"],
            "Unit": "Count",
        },
    ]

    for status in ("GREEN", "YELLOW", "RED"):
        metrics.append(
            {
                "MetricName": "DatasetHealthCount",
                "Dimensions": base_dimensions + [{"Name": "Status", "Value": status}],
                "Value": summary[status],
                "Unit": "Count",
            }
        )

    if include_datasets:
        for dataset_report in report.datasets:
            metrics.append(
                {
                    "MetricName": "DatasetHealthDatasetStatus",
                    "Dimensions": base_dimensions
                    + [{"Name": "Dataset", "Value": dataset_report.dataset.name}],
                    "Value": status_value(dataset_report.status),
                    "Unit": "None",
                }
            )

    return metrics


def emit_cloudwatch_metrics(
    report: HealthReport,
    namespace: str,
    base_dimensions: List[Dict[str, str]],
    region: Optional[str] = None,
    include_datasets: bool = True,
) -> int:
    try:
        import boto3
    except ImportError as exc:  # pragma: no cover - depends on optional dependency
        raise RuntimeError(
            "CloudWatch output requires boto3. Install with: pip install -e '.[aws]'"
        ) from exc

    metrics = build_cloudwatch_metrics(
        report, base_dimensions=base_dimensions, include_datasets=include_datasets
    )

    client = boto3.client("cloudwatch", region_name=region)
    chunk_size = 20
    for idx in range(0, len(metrics), chunk_size):
        client.put_metric_data(
            Namespace=namespace,
            MetricData=metrics[idx : idx + chunk_size],
        )
    return len(metrics)
