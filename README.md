# Dataset Health Monitoring

This repository hosts **Dataset Health**, an open source, plugin-friendly
library and service that evaluates dataset quality signals such as freshness,
completeness, schema drift, and volume. It produces a concise health status
(GREEN | YELLOW | RED) along with JSON and HTML reports that teams can share
or embed into monitoring workflows.

## Repository layout

- `dataset-health/` — Python package and CLI implementation
- `dataset-health/examples/` — sample datasets and rendered HTML report

## Quick start

```bash
cd dataset-health
pip install -e .
python src/cli.py --datasets datasets --out-json health.json --out-html health.html
```

Or run the installed CLI:

```bash
dataset-health --datasets datasets --out-json health.json --out-html health.html
```

## Sample report

Generate a full report with the bundled sample datasets:

```bash
python src/cli.py \
  --datasets examples/sample_datasets.yaml \
  --out-json examples/health.json \
  --out-html examples/health.html \
  --now 2026-02-07T18:30:00Z
```

The generated HTML is stored at:

- `dataset-health/examples/health.html`

## Plugins

Checks are pluggable via Python entry points under the
`dataset_health.checks` group. See `dataset-health/README.md` for the full
plugin specification and additional details.
