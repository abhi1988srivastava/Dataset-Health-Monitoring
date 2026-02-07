from __future__ import annotations

from datetime import datetime, timezone
import textwrap

from registry import DatasetRegistry, parse_datetime


def test_parse_datetime_iso_z() -> None:
    value = parse_datetime("2026-02-07T18:30:00Z")
    assert value is not None
    assert value.tzinfo == timezone.utc
    assert value.isoformat() == "2026-02-07T18:30:00+00:00"


def test_parse_datetime_timestamp() -> None:
    value = parse_datetime(0)
    assert value == datetime(1970, 1, 1, tzinfo=timezone.utc)


def test_dataset_registry_loads_list(tmp_path) -> None:
    content = """
    - name: alpha
      location: s3://alpha
    - name: beta
      location: s3://beta
    """
    path = tmp_path / "datasets.yaml"
    path.write_text(textwrap.dedent(content).strip())

    registry = DatasetRegistry()
    registry.load_from_path(path)

    names = [dataset.name for dataset in registry.list()]
    assert names == ["alpha", "beta"]


def test_dataset_registry_loads_single(tmp_path) -> None:
    content = """
    name: gamma
    location: s3://gamma
    owner: analytics
    """
    path = tmp_path / "dataset.yaml"
    path.write_text(textwrap.dedent(content).strip())

    registry = DatasetRegistry()
    registry.load_from_path(path)
    datasets = registry.list()

    assert len(datasets) == 1
    assert datasets[0].name == "gamma"
    assert datasets[0].location == "s3://gamma"
