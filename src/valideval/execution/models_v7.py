from __future__ import annotations

from pathlib import Path
from typing import Any

from valideval.execution.config import V6ConfigurationError, load_yaml_mapping

_ARCHITECTURES = {
    "Qwen/Qwen2.5-0.5B-Instruct": "qwen2",
    "Qwen/Qwen2.5-1.5B-Instruct": "qwen2",
    "Qwen/Qwen2.5-3B-Instruct": "qwen2",
    "microsoft/Phi-3-mini-4k-instruct": "phi3",
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0": "llama",
    "HuggingFaceTB/SmolLM2-1.7B-Instruct": "llama",
    "allenai/OLMo-2-0425-1B-Instruct": "olmo2",
    "ibm-granite/granite-3.3-2b-instruct": "granite",
    "stabilityai/stablelm-2-1_6b-chat": "stablelm",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B": "qwen2",
    "mistralai/Mistral-7B-Instruct-v0.3": "mistral",
    "meta-llama/Llama-3.2-1B-Instruct": "llama",
    "google/gemma-2-2b-it": "gemma2",
}
_HEX = frozenset("0123456789abcdef")


def load_panel_config_v7(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    panel = load_yaml_mapping(source)
    if str(panel.get("schema_version")) != "7.0":
        raise V6ConfigurationError("V7 panel must declare schema_version: '7.0'")
    required = {"panel_id", "study_id", "evidence_class", "model_count", "family_count"}
    missing = sorted(required.difference(panel))
    if missing:
        raise V6ConfigurationError(f"V7 panel config missing fields: {missing}")

    models: list[dict[str, Any]] = []
    inherited = panel.get("inherits_exact_models_from")
    if inherited:
        root = _repository_root(source)
        base_path = (root / str(inherited)).resolve()
        if not base_path.is_relative_to(root):
            raise V6ConfigurationError("inherited panel leaves repository root")
        base = load_panel_config_v7(base_path)
        models.extend(dict(model) for model in base["models"])
    raw_models = panel.get("models", [])
    extensions = panel.get("extensions", [])
    if not isinstance(raw_models, list) or not isinstance(extensions, list):
        raise V6ConfigurationError("V7 panel models and extensions must be lists")
    models.extend(_normalize_model(model) for model in [*raw_models, *extensions])
    if not models:
        raise V6ConfigurationError("V7 panel has no resolved models")

    seen: set[str] = set()
    for model in models:
        identifier = str(model["canonical_model_id"])
        if identifier in seen:
            raise V6ConfigurationError(f"duplicate V7 panel model: {identifier}")
        seen.add(identifier)
    declared_count = int(panel.get("maximum_model_count", panel["model_count"]))
    declared_families = int(panel.get("maximum_family_count", panel["family_count"]))
    families = {str(model["family"]) for model in models}
    if len(models) != declared_count:
        raise V6ConfigurationError(
            f"V7 panel model count mismatch: declared {declared_count}, resolved {len(models)}"
        )
    if len(families) != declared_families:
        raise V6ConfigurationError(
            f"V7 panel family count mismatch: declared {declared_families}, "
            f"resolved {len(families)}"
        )
    allowed = panel.get("allowed_model_repositories")
    if allowed is not None and set(map(str, allowed)) != seen:
        raise V6ConfigurationError("fallback panel allowlist does not match inherited models")
    return {
        **panel,
        "models": models,
        "model_count": len(models),
        "family_count": len(families),
    }


def _normalize_model(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise V6ConfigurationError("V7 panel model entries must be mappings")
    required = {
        "repository",
        "revision",
        "family",
        "parameters",
        "license",
        "dtype",
        "quantization_fallback",
        "expected_download_gb",
        "expected_vram_gb",
    }
    missing = sorted(required.difference(raw))
    if missing:
        raise V6ConfigurationError(f"V7 model {raw.get('repository')} missing fields: {missing}")
    repository = str(raw["repository"])
    revision = str(raw["revision"])
    if repository not in _ARCHITECTURES:
        raise V6ConfigurationError(f"V7 model is absent from the audited registry: {repository}")
    if len(revision) != 40 or any(character not in _HEX for character in revision):
        raise V6ConfigurationError(f"V7 model revision is not immutable: {repository}")
    quantization = str(raw.get("quantization", "none")).lower()
    fallback = raw.get("quantization_fallback")
    if fallback == "bitsandbytes_nf4":
        fallback = "nf4"
    if quantization not in {"none", "unquantized", "nf4", "int4"}:
        raise V6ConfigurationError(f"unsupported quantization for {repository}")
    if fallback not in {None, "nf4", "int4"}:
        raise V6ConfigurationError(f"unsupported quantization fallback for {repository}")
    access = str(raw.get("access", "public"))
    return {
        **raw,
        "canonical_model_id": repository,
        "tokenizer_revision": revision,
        "architecture": _ARCHITECTURES[repository],
        "parameter_count": int(raw["parameters"]),
        "quantization": quantization,
        "quantization_fallback": fallback,
        "max_memory": "14GiB",
        "trust_remote_code": False,
        "remote_code_registry_approved": False,
        "chat_template_policy": f"tokenizer_template_at_{revision}",
        "expected_t4_feasibility": "REQUIRES_S2_EMPIRICAL_PREFLIGHT",
        "expected_download_size": int(float(raw["expected_download_gb"]) * 1024**3),
        "access": access,
    }


def _repository_root(source: Path) -> Path:
    for parent in (source.resolve().parent, *source.resolve().parents):
        if (parent / "pyproject.toml").is_file():
            return parent
    raise V6ConfigurationError(f"could not resolve repository root from panel {source}")
