from __future__ import annotations

from html import escape
import json
from typing import Any, Dict, Iterable, List

from health import HealthReport


def _format_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True)
    return str(value)


def _status_class(status: str) -> str:
    return status.lower()


def render_html(report: HealthReport, title: str = "Dataset Health") -> str:
    summary = report.summary()

    lines: List[str] = [
        "<!doctype html>",
        "<html lang=\"en\">",
        "<head>",
        "  <meta charset=\"utf-8\" />",
        f"  <title>{escape(title)}</title>",
        "  <style>",
        "    :root {",
        "      --green: #1f7a1f;",
        "      --yellow: #b36b00;",
        "      --red: #b00020;",
        "      --bg: #f6f7fb;",
        "      --card: #ffffff;",
        "      --text: #1b1f24;",
        "      --muted: #5d6771;",
        "    }",
        "    * { box-sizing: border-box; }",
        "    body {",
        "      margin: 0;",
        "      font-family: Arial, sans-serif;",
        "      color: var(--text);",
        "      background: var(--bg);",
        "    }",
        "    .container {",
        "      max-width: 1100px;",
        "      margin: 0 auto;",
        "      padding: 32px 24px 60px;",
        "    }",
        "    header {",
        "      display: flex;",
        "      align-items: baseline;",
        "      justify-content: space-between;",
        "      flex-wrap: wrap;",
        "      gap: 12px;",
        "    }",
        "    h1 { margin: 0; font-size: 28px; }",
        "    .muted { color: var(--muted); font-size: 14px; }",
        "    .summary {",
        "      display: grid;",
        "      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));",
        "      gap: 16px;",
        "      margin: 24px 0;",
        "    }",
        "    .card {",
        "      background: var(--card);",
        "      padding: 16px;",
        "      border-radius: 10px;",
        "      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);",
        "    }",
        "    .card h2 { margin: 0 0 6px; font-size: 18px; }",
        "    .status-pill {",
        "      display: inline-flex;",
        "      align-items: center;",
        "      gap: 6px;",
        "      font-weight: 600;",
        "      padding: 4px 10px;",
        "      border-radius: 999px;",
        "      font-size: 12px;",
        "      letter-spacing: 0.04em;",
        "    }",
        "    .status-pill.green { background: rgba(31, 122, 31, 0.12); color: var(--green); }",
        "    .status-pill.yellow { background: rgba(179, 107, 0, 0.12); color: var(--yellow); }",
        "    .status-pill.red { background: rgba(176, 0, 32, 0.12); color: var(--red); }",
        "    .dataset {",
        "      background: var(--card);",
        "      border-radius: 12px;",
        "      padding: 20px;",
        "      margin-bottom: 20px;",
        "      border-left: 6px solid transparent;",
        "    }",
        "    .dataset.green { border-left-color: var(--green); }",
        "    .dataset.yellow { border-left-color: var(--yellow); }",
        "    .dataset.red { border-left-color: var(--red); }",
        "    .dataset-header {",
        "      display: flex;",
        "      align-items: center;",
        "      justify-content: space-between;",
        "      gap: 12px;",
        "      flex-wrap: wrap;",
        "    }",
        "    .dataset-header h2 { margin: 0; font-size: 20px; }",
        "    .meta-grid {",
        "      display: grid;",
        "      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));",
        "      gap: 10px 20px;",
        "      margin: 14px 0 18px;",
        "      font-size: 14px;",
        "    }",
        "    .meta-grid div span { color: var(--muted); }",
        "    table { width: 100%; border-collapse: collapse; }",
        "    th, td { text-align: left; padding: 10px 8px; font-size: 14px; }",
        "    th { border-bottom: 1px solid #e0e4ea; color: var(--muted); }",
        "    tr + tr td { border-top: 1px solid #f0f2f5; }",
        "    details { margin-top: 6px; }",
        "    pre {",
        "      background: #f4f5f8;",
        "      padding: 10px;",
        "      border-radius: 8px;",
        "      overflow-x: auto;",
        "      font-size: 12px;",
        "    }",
        "  </style>",
        "</head>",
        "<body>",
        "  <div class=\"container\">",
        "    <header>",
        f"      <h1>{escape(title)}</h1>",
        f"      <div class=\"muted\">Generated at {escape(report.generated_at.isoformat())}</div>",
        "    </header>",
        "    <section class=\"summary\">",
        f"      <div class=\"card\"><h2>Total</h2><div>{summary['total']}</div></div>",
        f"      <div class=\"card\"><h2>Green</h2><div>{summary['GREEN']}</div></div>",
        f"      <div class=\"card\"><h2>Yellow</h2><div>{summary['YELLOW']}</div></div>",
        f"      <div class=\"card\"><h2>Red</h2><div>{summary['RED']}</div></div>",
        "    </section>",
    ]

    for dataset_report in report.datasets:
        dataset = dataset_report.dataset
        status_value = dataset_report.status.value
        status_class = _status_class(status_value)
        lines.extend(
            [
                f"    <section class=\"dataset {status_class}\">",
                "      <div class=\"dataset-header\">",
                f"        <h2>{escape(dataset.name)}</h2>",
                f"        <span class=\"status-pill {status_class}\">{escape(status_value)}</span>",
                "      </div>",
                "      <div class=\"meta-grid\">",
                f"        <div><span>Description:</span> {escape(dataset.description or '-')}</div>",
                f"        <div><span>Location:</span> {escape(dataset.location or '-')}</div>",
                f"        <div><span>Owner:</span> {escape(dataset.owner or '-')}</div>",
                f"        <div><span>Source:</span> {escape(dataset.source or '-')}</div>",
                f"        <div><span>Last Updated:</span> {escape(_format_value(dataset.get('last_updated')))}</div>",
                "      </div>",
                "      <table>",
                "        <thead>",
                "          <tr>",
                "            <th>Check</th>",
                "            <th>Status</th>",
                "            <th>Message</th>",
                "            <th>Details</th>",
                "          </tr>",
                "        </thead>",
                "        <tbody>",
            ]
        )

        for check in dataset_report.checks:
            check_status = check.status.value
            details_payload = check.details or {}
            if details_payload:
                details_text = escape(json.dumps(details_payload, indent=2, ensure_ascii=True, sort_keys=True))
                details_html = (
                    "<details><summary>View</summary>"
                    f"<pre>{details_text}</pre>"
                    "</details>"
                )
            else:
                details_html = "-"
            lines.extend(
                [
                    "          <tr>",
                    f"            <td>{escape(check.name)}</td>",
                    f"            <td><span class=\"status-pill {_status_class(check_status)}\">{escape(check_status)}</span></td>",
                    f"            <td>{escape(check.message)}</td>",
                    f"            <td>{details_html}</td>",
                    "          </tr>",
                ]
            )

        lines.extend(
            [
                "        </tbody>",
                "      </table>",
                "    </section>",
            ]
        )

    lines.extend(["  </div>", "</body>", "</html>"])
    return "\n".join(lines)
