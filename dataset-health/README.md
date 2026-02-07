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

Or run the installed CLI:

```bash
dataset-health --datasets datasets --out-json health.json --out-html health.html
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

### Sample datasets for a full report

The repository includes a richer sample set to exercise different outcomes:

```bash
python src/cli.py \
  --datasets examples/sample_datasets.yaml \
  --out-json examples/health.json \
  --out-html examples/health.html \
  --now 2026-02-07T18:30:00Z
```

The `--now` flag makes results deterministic so you can compare outputs.

## Automation outputs

Use `--output` to select a single, machine-friendly format:

- `report-json` (full report, default)
- `summary-json` (compact counts + overall status)
- `jsonl` (one dataset per line)
- `prometheus` (text exposition format)
- `cloudwatch` (pushes metrics to AWS CloudWatch)

### Summary JSON

```bash
python src/cli.py \
  --datasets examples/sample_datasets.yaml \
  --output summary-json \
  --stdout
```

### JSON Lines

```bash
python src/cli.py \
  --datasets examples/sample_datasets.yaml \
  --output jsonl \
  --out examples/health.jsonl
```

### Prometheus

```bash
python src/cli.py \
  --datasets examples/sample_datasets.yaml \
  --output prometheus \
  --stdout
```

### CloudWatch

```bash
pip install -e ".[aws]"
python src/cli.py \
  --datasets examples/sample_datasets.yaml \
  --output cloudwatch \
  --cloudwatch-namespace DatasetHealth \
  --cloudwatch-dimensions env=dev,team=data-platform
```

### Exit codes for automation

Use `--fail-on` to signal failures to CI/CD or schedulers:

- `--fail-on red` exits with code 2 on RED
- `--fail-on yellow` exits with code 2 on YELLOW or RED

```bash
python src/cli.py \
  --datasets examples/sample_datasets.yaml \
  --output summary-json \
  --stdout \
  --fail-on red
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

## Testing

```bash
pip install -e ".[test]"
pytest
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
