from __future__ import annotations

import gc
import hashlib
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from valideval.execution.config import V6ConfigurationError, load_yaml_mapping
from valideval.execution.datasets import reject_gold_fields

SUPPORTED_ARCHITECTURES = frozenset(
    {"qwen2", "phi3", "llama", "olmo2", "granite", "stablelm", "mistral", "gemma2"}
)


class ModelResolutionError(RuntimeError):
    """Raised when an exact checkpoint cannot be loaded under the frozen condition."""


class TextGenerator(Protocol):
    model_load_seconds: float
    cache_status: str

    def generate(self, prompt: str, generation: Mapping[str, Any]) -> dict[str, Any]: ...

    def score_choices(
        self, prompt: str, choices: tuple[str, ...], generation: Mapping[str, Any]
    ) -> dict[str, Any]: ...

    def close(self) -> None: ...


@dataclass(slots=True)
class MockTextGenerator:
    """Deterministic non-evidence adapter for production-path integration tests."""

    benchmark_id: str
    model_load_seconds: float = 0.0
    cache_status: str = "NON_EVIDENCE_FIXTURE"

    def generate(self, prompt: str, generation: Mapping[str, Any]) -> dict[str, Any]:
        reject_gold_fields({"prompt": prompt})
        started = time.perf_counter()
        selector = int(hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8], 16)
        if self.benchmark_id == "mmlu":
            raw = "ABCD"[selector % 4]
        elif self.benchmark_id == "gsm8k":
            raw = f"Final answer: {selector % 101}"
        else:
            raw = "Final answer: (A)"
        return {
            "raw_output": raw,
            "input_tokens": len(prompt.split()),
            "output_tokens": len(raw.split()),
            "generation_seconds": time.perf_counter() - started,
            "truncated": False,
        }

    def score_choices(
        self, prompt: str, choices: tuple[str, ...], generation: Mapping[str, Any]
    ) -> dict[str, Any]:
        reject_gold_fields({"prompt": prompt, "choices": choices})
        started = time.perf_counter()
        selector = int(hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:8], 16)
        raw = choices[selector % len(choices)]
        return {
            "raw_output": raw,
            "input_tokens": len(prompt.split()),
            "output_tokens": 1,
            "generation_seconds": time.perf_counter() - started,
            "truncated": False,
            "choice_scores": {choice: float(choice == raw) for choice in choices},
        }

    def close(self) -> None:
        return None


class TransformersTextGenerator:
    def __init__(
        self,
        model_record: Mapping[str, Any],
        *,
        gpu_id: str,
        cache_dir: str | Path | None,
    ) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise ModelResolutionError(
                "transformers and torch are required; install requirements-kaggle-t4x2-v6.txt"
            ) from exc

        repository = str(model_record["repository"])
        revision = str(model_record["revision"])
        tokenizer_revision = str(model_record["tokenizer_revision"])
        trust_remote_code = bool(model_record.get("trust_remote_code", False))
        if trust_remote_code and not bool(model_record.get("remote_code_registry_approved", False)):
            raise ModelResolutionError(
                f"remote code is not registry-approved for {repository}@{revision}"
            )
        architecture = str(model_record.get("architecture", ""))
        if architecture not in SUPPORTED_ARCHITECTURES:
            raise ModelResolutionError(
                f"unsupported architecture {architecture!r} for {repository}"
            )
        dtype_name = str(model_record["dtype"]).lower()
        dtype_by_name = {
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
            "float32": torch.float32,
        }
        if dtype_name not in dtype_by_name:
            raise ModelResolutionError(f"unsupported dtype: {dtype_name}")
        quantization = str(model_record.get("quantization", "none")).lower()
        model_kwargs: dict[str, Any] = {
            "revision": revision,
            "trust_remote_code": trust_remote_code,
            "torch_dtype": dtype_by_name[dtype_name],
            "cache_dir": str(cache_dir) if cache_dir else None,
            "low_cpu_mem_usage": True,
        }
        if quantization not in {"none", "unquantized"}:
            if quantization not in {"nf4", "int4"}:
                raise ModelResolutionError(f"unsupported quantization: {quantization}")
            try:
                from transformers import BitsAndBytesConfig
            except ImportError as exc:
                raise ModelResolutionError("BitsAndBytes quantization is unavailable") from exc
            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=dtype_by_name[dtype_name],
            )
        self.cache_status = _cache_status(repository, revision, cache_dir)
        started = time.perf_counter()
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                repository,
                revision=tokenizer_revision,
                trust_remote_code=trust_remote_code,
                cache_dir=str(cache_dir) if cache_dir else None,
                use_fast=True,
            )
            self.model = AutoModelForCausalLM.from_pretrained(repository, **model_kwargs)
            if quantization in {"none", "unquantized"}:
                self.model.to("cuda:0")
            self.model.eval()
        except Exception as exc:
            raise ModelResolutionError(
                f"failed to load exact checkpoint {repository}@{revision}: {exc}"
            ) from exc
        self.model_load_seconds = time.perf_counter() - started
        self.gpu_id = gpu_id

    def generate(self, prompt: str, generation: Mapping[str, Any]) -> dict[str, Any]:
        reject_gold_fields({"prompt": prompt})
        import torch

        messages = [{"role": "user", "content": prompt}]
        if not hasattr(self.tokenizer, "apply_chat_template"):
            raise ModelResolutionError("tokenizer does not expose a chat template")
        rendered = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        encoded = self.tokenizer(
            rendered,
            return_tensors="pt",
            truncation=True,
            max_length=int(generation.get("max_input_tokens", 4096)),
        )
        encoded = {key: value.to("cuda:0") for key, value in encoded.items()}
        max_new_tokens = int(generation["max_new_tokens"])
        started = time.perf_counter()
        do_sample = bool(generation.get("do_sample", False))
        generation_kwargs: dict[str, Any] = {
            "do_sample": do_sample,
            "max_new_tokens": max_new_tokens,
            "pad_token_id": self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
        }
        if do_sample:
            torch.manual_seed(int(generation.get("seed", 0)))
            generation_kwargs.update(
                {
                    "temperature": float(generation.get("temperature", 1.0)),
                    "top_p": float(generation.get("top_p", 1.0)),
                }
            )
        with torch.inference_mode():
            outputs = self.model.generate(**encoded, **generation_kwargs)
        elapsed = time.perf_counter() - started
        input_count = int(encoded["input_ids"].shape[-1])
        generated = outputs[0, input_count:]
        output_count = int(generated.shape[-1])
        raw = self.tokenizer.decode(generated, skip_special_tokens=True)
        eos_token_id = self.tokenizer.eos_token_id
        ended_with_eos = bool(
            output_count and eos_token_id is not None and int(generated[-1]) == int(eos_token_id)
        )
        return {
            "raw_output": raw,
            "input_tokens": input_count,
            "output_tokens": output_count,
            "generation_seconds": elapsed,
            "truncated": output_count >= max_new_tokens and not ended_with_eos,
        }

    def score_choices(
        self, prompt: str, choices: tuple[str, ...], generation: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Score frozen answer labels by mean conditional token log likelihood."""

        reject_gold_fields({"prompt": prompt, "choices": choices})
        import torch

        messages = [{"role": "user", "content": prompt}]
        rendered = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        prompt_ids = self.tokenizer(
            rendered,
            add_special_tokens=False,
            truncation=True,
            max_length=int(generation.get("max_input_tokens", 4096)),
        )["input_ids"]
        scores: dict[str, float] = {}
        started = time.perf_counter()
        with torch.inference_mode():
            for choice in choices:
                choice_ids = self.tokenizer(f" {choice}", add_special_tokens=False)["input_ids"]
                if not choice_ids:
                    raise ModelResolutionError(f"empty choice tokenization for {choice!r}")
                input_ids = torch.tensor([prompt_ids + choice_ids], device="cuda:0")
                logits = self.model(input_ids=input_ids).logits[0]
                log_probs = torch.log_softmax(logits, dim=-1)
                start = len(prompt_ids) - 1
                token_scores = [
                    float(log_probs[start + offset, token_id].item())
                    for offset, token_id in enumerate(choice_ids)
                ]
                scores[choice] = sum(token_scores) / len(token_scores)
        best = max(sorted(scores), key=scores.__getitem__)
        return {
            "raw_output": best,
            "input_tokens": len(prompt_ids),
            "output_tokens": 1,
            "generation_seconds": time.perf_counter() - started,
            "truncated": False,
            "choice_scores": scores,
        }

    def close(self) -> None:
        try:
            del self.model
            del self.tokenizer
        finally:
            gc.collect()
            try:
                import torch

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass


def load_panel_config(path: str | Path) -> dict[str, Any]:
    panel = load_yaml_mapping(path)
    if str(panel.get("schema_version")) == "7.0":
        from valideval.execution.models_v7 import load_panel_config_v7

        return load_panel_config_v7(path)
    required = {
        "panel_id",
        "study_id",
        "evidence_class",
        "scientific_panel_adequacy",
        "models",
    }
    missing = sorted(required.difference(panel))
    if missing:
        raise V6ConfigurationError(f"panel config missing fields: {missing}")
    if panel["evidence_class"] != "ENGINEERING_ONLY":
        raise V6ConfigurationError("S1 panel must declare evidence_class: ENGINEERING_ONLY")
    if panel["scientific_panel_adequacy"] is not False:
        raise V6ConfigurationError("S1 panel must declare scientific_panel_adequacy: false")
    models = panel["models"]
    if not isinstance(models, list) or len(models) != 5:
        raise V6ConfigurationError("S1 panel must contain exactly five models")
    required_model_fields = {
        "canonical_model_id",
        "repository",
        "revision",
        "tokenizer_revision",
        "family",
        "parameter_count",
        "dtype",
        "quantization",
        "quantization_fallback",
        "max_memory",
        "trust_remote_code",
        "chat_template_policy",
        "license",
        "expected_t4_feasibility",
        "expected_download_size",
        "architecture",
    }
    seen: set[str] = set()
    for model in models:
        if not isinstance(model, dict):
            raise V6ConfigurationError("panel model entries must be mappings")
        missing_model = sorted(required_model_fields.difference(model))
        if missing_model:
            raise V6ConfigurationError(
                f"model {model.get('canonical_model_id')} missing fields: {missing_model}"
            )
        identifier = str(model["canonical_model_id"])
        if identifier in seen:
            raise V6ConfigurationError(f"duplicate panel model: {identifier}")
        seen.add(identifier)
        revision = str(model["revision"])
        if len(revision) != 40 or any(char not in "0123456789abcdef" for char in revision):
            raise V6ConfigurationError(f"model revision is not an immutable commit: {identifier}")
        tokenizer_revision = str(model["tokenizer_revision"])
        if len(tokenizer_revision) != 40 or any(
            char not in "0123456789abcdef" for char in tokenizer_revision
        ):
            raise V6ConfigurationError(
                f"tokenizer revision is not an immutable commit: {identifier}"
            )
        if str(model["repository"]) != identifier:
            raise V6ConfigurationError(f"repository and canonical model ID disagree: {identifier}")
        if str(model["architecture"]) not in SUPPORTED_ARCHITECTURES:
            raise V6ConfigurationError(f"unsupported architecture for {identifier}")
        if bool(model["trust_remote_code"]) and not bool(
            model.get("remote_code_registry_approved", False)
        ):
            raise V6ConfigurationError(f"unsafe unapproved remote code for {identifier}")
        if str(model["dtype"]).lower() not in {"float16", "bfloat16", "float32"}:
            raise V6ConfigurationError(f"unsupported dtype for {identifier}")
        if str(model["quantization"]).lower() not in {
            "none",
            "unquantized",
            "nf4",
            "int4",
        }:
            raise V6ConfigurationError(f"unsupported quantization for {identifier}")
        if int(model["expected_download_size"]) <= 0:
            raise V6ConfigurationError(f"invalid expected download size for {identifier}")
        if model["expected_t4_feasibility"] not in {"EXPECTED_FIT_UNVERIFIED_UNTIL_S1"}:
            raise V6ConfigurationError(f"invalid T4 feasibility declaration for {identifier}")
    return panel


def build_text_generator(
    model_record: Mapping[str, Any],
    *,
    backend: str,
    benchmark_id: str,
    gpu_id: str,
    cache_dir: str | Path | None,
) -> TextGenerator:
    if backend == "mock":
        return MockTextGenerator(benchmark_id=benchmark_id)
    if backend == "transformers":
        return TransformersTextGenerator(model_record, gpu_id=gpu_id, cache_dir=cache_dir)
    raise ModelResolutionError(f"unknown model backend: {backend}")


def _cache_status(repository: str, revision: str, cache_dir: str | Path | None) -> str:
    if cache_dir is None:
        return "unknown"
    root = Path(cache_dir)
    repository_dir = root / f"models--{repository.replace('/', '--')}" / "snapshots" / revision
    return "hit" if repository_dir.is_dir() else "miss"
