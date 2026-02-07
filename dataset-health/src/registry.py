from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import importlib
import importlib.metadata
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import yaml


class Status(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: Status
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
        }


@dataclass(frozen=True)
class Dataset:
    name: str
    description: str = ""
    location: str = ""
    owner: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""

    def get(self, key: str, default: Any = None) -> Any:
        return self.metadata.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "owner": self.owner,
            "source": self.source,
        }
        payload.update(self.metadata)
        return payload


@dataclass(frozen=True)
class CheckSpec:
    name: str
    description: str
    runner: Callable[[Dataset, datetime], CheckResult]


class CheckRegistry:
    def __init__(self) -> None:
        self._checks: Dict[str, CheckSpec] = {}

    def register(self, name: str, description: str, runner: Callable[[Dataset, datetime], CheckResult]) -> None:
        if name in self._checks:
            raise ValueError(f"Check already registered: {name}")
        self._checks[name] = CheckSpec(name=name, description=description, runner=runner)

    def list(self) -> List[CheckSpec]:
        return [self._checks[name] for name in sorted(self._checks)]

    def run_all(self, dataset: Dataset, now: datetime) -> List[CheckResult]:
        results: List[CheckResult] = []
        for spec in self.list():
            result = spec.runner(dataset, now)
            if not isinstance(result, CheckResult):
                raise ValueError(f"Check {spec.name} returned invalid result type")
            results.append(result)
        return results


CHECK_REGISTRY = CheckRegistry()


def register_check(name: str, description: str) -> Callable[[Callable[[Dataset, datetime], CheckResult]], Callable[[Dataset, datetime], CheckResult]]:
    def decorator(func: Callable[[Dataset, datetime], CheckResult]) -> Callable[[Dataset, datetime], CheckResult]:
        CHECK_REGISTRY.register(name=name, description=description, runner=func)
        return func

    return decorator


class DatasetRegistry:
    def __init__(self) -> None:
        self._datasets: Dict[str, Dataset] = {}

    def add(self, dataset: Dataset) -> None:
        if dataset.name in self._datasets:
            raise ValueError(f"Dataset already registered: {dataset.name}")
        self._datasets[dataset.name] = dataset

    def list(self) -> List[Dataset]:
        return [self._datasets[name] for name in sorted(self._datasets)]

    def load_from_path(self, path: Path) -> None:
        if path.is_dir():
            files = sorted({*path.glob("*.yaml"), *path.glob("*.yml")})
            for file_path in files:
                self._load_file(file_path)
            return
        if path.is_file():
            self._load_file(path)
            return
        raise FileNotFoundError(f"Dataset path not found: {path}")

    def _load_file(self, path: Path) -> None:
        payload = yaml.safe_load(path.read_text()) or {}
        if isinstance(payload, list):
            datasets = payload
        elif isinstance(payload, dict):
            datasets = [payload]
        else:
            raise ValueError(f"Invalid dataset definition in {path}")
        for dataset_payload in datasets:
            dataset = _dataset_from_dict(dataset_payload, source=str(path))
            self.add(dataset)


def _dataset_from_dict(payload: Dict[str, Any], source: str) -> Dataset:
    if not isinstance(payload, dict):
        raise ValueError("Dataset entry must be a mapping")
    name = str(payload.get("name") or "").strip()
    if not name:
        raise ValueError("Dataset entry missing required field: name")
    description = str(payload.get("description") or "")
    location = str(payload.get("location") or "")
    owner = str(payload.get("owner") or "")
    metadata = {
        key: value
        for key, value in payload.items()
        if key not in {"name", "description", "location", "owner"}
    }
    return Dataset(
        name=name,
        description=description,
        location=location,
        owner=owner,
        metadata=metadata,
        source=source,
    )


def parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    return None


def load_builtin_checks() -> None:
    for module in ("checks.freshness", "checks.completeness", "checks.schema", "checks.volume"):
        importlib.import_module(module)


def load_entrypoint_checks(
    registry: CheckRegistry = CHECK_REGISTRY,
    group: str = "dataset_health.checks",
) -> Tuple[int, List[str]]:
    errors: List[str] = []
    count = 0
    try:
        entry_points = importlib.metadata.entry_points()
    except Exception as exc:  # pragma: no cover - defensive
        return 0, [f"Failed to load entry points: {exc}"]

    if hasattr(entry_points, "select"):
        selected = entry_points.select(group=group)
    else:  # pragma: no cover - older importlib.metadata
        selected = entry_points.get(group, [])

    for entry_point in selected:
        try:
            plugin = entry_point.load()
            if isinstance(plugin, CheckSpec):
                registry.register(plugin.name, plugin.description, plugin.runner)
            elif callable(plugin):
                description = (plugin.__doc__ or "Entry point plugin.").strip()
                registry.register(entry_point.name, description, plugin)
            else:
                raise TypeError("Entry point must be callable or CheckSpec")
            count += 1
        except Exception as exc:  # pragma: no cover - plugin errors vary
            errors.append(f"{entry_point.name}: {exc}")
    return count, errors
