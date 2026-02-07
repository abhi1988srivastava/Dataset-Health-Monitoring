# Dataset Health

Dataset Health is an open source library and plugin-friendly service for
tracking dataset quality over time. It focuses on clear, actionable signals
that teams can plug into their pipelines and monitoring stacks.

## What it tracks

- Dataset registry (S3 / GCS / local metadata)
- Freshness
- Completeness
- Schema drift
- Volume
- Policy compliance via plugins

## Outputs

- Dataset health status: **GREEN | YELLOW | RED**
- JSON report
- HTML report

## Quick start

```bash
pip install -e .
python src/cli.py --datasets datasets --out-json health.json --out-html health.html
```

### Example dataset definition

```yaml
name: user_events
description: Daily user events snapshot
location: s3://analytics/user_events/
owner: data-platform
last_updated: "2026-02-06T18:30:00Z"
freshness_hours: 24
record_count: 980000
expected_min_records: 1000000
schema:
  - id
  - user_id
  - event_type
  - ts
expected_schema:
  - id
  - user_id
  - event_type
  - ts
  - device
bytes: 987654321
expected_min_bytes: 900000000
```

## Plugin model

Checks are pluggable. A check is a callable that returns a `CheckResult`.
Built-in checks live under `src/checks/`, and external plugins can register
via Python entry points in the `dataset_health.checks` group.

Example entry point declaration:

```toml
[project.entry-points."dataset_health.checks"]
policy_compliance = "my_package.policy:check_policy"
```

The function signature should be:

```python
def check_policy(dataset, now):
    ...
    return CheckResult(...)
```

## Project layout

```
dataset-health/
├── README.md
├── datasets/
│   └── user_events.yaml
├── src/
│   ├── registry.py
│   ├── checks/
│   │   ├── freshness.py
│   │   ├── completeness.py
│   │   ├── schema.py
│   │   └── volume.py
│   ├── health.py
│   ├── explain.py
│   └── cli.py
├── examples/
├── tests/
└── pyproject.toml
```
