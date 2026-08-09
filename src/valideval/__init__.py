"""Validity auditing tools for AI benchmark measurement claims."""

from valideval.plugins import (
    benchmark_loader,
    diagnostic,
    domain_pack,
    extractor,
    get_plugin,
    list_plugins,
    model_runner,
    register_plugin,
    repair_policy,
    report_section,
    scorer,
    visualization,
)

__version__ = "0.4.0"

__all__ = [
    "__version__",
    "benchmark_loader",
    "diagnostic",
    "domain_pack",
    "extractor",
    "get_plugin",
    "list_plugins",
    "model_runner",
    "register_plugin",
    "repair_policy",
    "report_section",
    "scorer",
    "visualization",
]
