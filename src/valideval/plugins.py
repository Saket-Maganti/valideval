from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

T = TypeVar("T")

PLUGIN_KINDS = (
    "benchmark_loader",
    "model_runner",
    "scorer",
    "extractor",
    "diagnostic",
    "report_section",
    "repair_policy",
    "domain_pack",
    "visualization",
)


@dataclass
class PluginRegistry:
    """Dependency-free registry for ValidEval extension points."""

    kind: str
    _entries: dict[str, Any] = field(default_factory=dict)

    def register(self, name: str, obj: T, *, replace: bool = False) -> T:
        normalized = _normalize_name(name)
        if normalized in self._entries and not replace:
            raise ValueError(f"{self.kind} plugin already registered: {normalized}")
        self._entries[normalized] = obj
        return obj

    def get(self, name: str) -> Any:
        normalized = _normalize_name(name)
        if normalized not in self._entries:
            raise KeyError(f"Unknown {self.kind} plugin: {normalized}")
        return self._entries[normalized]

    def list(self) -> list[str]:
        return sorted(self._entries)

    def items(self) -> dict[str, Any]:
        return dict(sorted(self._entries.items()))


REGISTRIES: dict[str, PluginRegistry] = {kind: PluginRegistry(kind) for kind in PLUGIN_KINDS}


def register_plugin(kind: str, name: str, obj: T | None = None, *, replace: bool = False):
    if kind not in REGISTRIES:
        raise KeyError(f"Unknown plugin kind: {kind}")

    def decorator(target: T) -> T:
        return REGISTRIES[kind].register(name, target, replace=replace)

    if obj is not None:
        return decorator(obj)
    return decorator


def get_plugin(kind: str, name: str) -> Any:
    if kind not in REGISTRIES:
        raise KeyError(f"Unknown plugin kind: {kind}")
    return REGISTRIES[kind].get(name)


def list_plugins(kind: str | None = None) -> dict[str, list[str]] | list[str]:
    if kind is not None:
        if kind not in REGISTRIES:
            raise KeyError(f"Unknown plugin kind: {kind}")
        return REGISTRIES[kind].list()
    return {name: registry.list() for name, registry in sorted(REGISTRIES.items())}


def benchmark_loader(name: str, *, replace: bool = False) -> Callable[[T], T]:
    return register_plugin("benchmark_loader", name, replace=replace)


def model_runner(name: str, *, replace: bool = False) -> Callable[[T], T]:
    return register_plugin("model_runner", name, replace=replace)


def scorer(name: str, *, replace: bool = False) -> Callable[[T], T]:
    return register_plugin("scorer", name, replace=replace)


def extractor(name: str, *, replace: bool = False) -> Callable[[T], T]:
    return register_plugin("extractor", name, replace=replace)


def diagnostic(name: str, *, replace: bool = False) -> Callable[[T], T]:
    return register_plugin("diagnostic", name, replace=replace)


def report_section(name: str, *, replace: bool = False) -> Callable[[T], T]:
    return register_plugin("report_section", name, replace=replace)


def repair_policy(name: str, *, replace: bool = False) -> Callable[[T], T]:
    return register_plugin("repair_policy", name, replace=replace)


def domain_pack(name: str, *, replace: bool = False) -> Callable[[T], T]:
    return register_plugin("domain_pack", name, replace=replace)


def visualization(name: str, *, replace: bool = False) -> Callable[[T], T]:
    return register_plugin("visualization", name, replace=replace)


def _normalize_name(name: str) -> str:
    normalized = str(name).strip().replace("-", "_")
    if not normalized:
        raise ValueError("Plugin name cannot be empty.")
    return normalized
