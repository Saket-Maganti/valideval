from __future__ import annotations

from typing import Any


def advise_benchmark_selection(goal: str) -> dict[str, Any]:
    text = goal.lower()
    domain = _domain_for_goal(text)
    return {
        "goal": goal,
        "recommended_domain_pack": domain,
        "benchmark_types": _benchmark_types(domain),
        "minimum_diagnostics": _minimum_diagnostics(domain),
        "possible_validity_threats": _threats(domain),
        "safe_claims": _safe_claims(domain),
        "unsafe_claims": [
            "This benchmark proves true model ability.",
            "A single score is a complete validity assessment.",
            "No local contamination evidence proves the benchmark is clean.",
        ],
        "needed_validation_evidence": _needed_evidence(domain),
        "limitations": [
            "Advisor output is planning guidance. It is not empirical evidence about any benchmark."
        ],
    }


def _domain_for_goal(goal: str) -> str:
    if any(token in goal for token in ["rag", "retrieval", "faithfulness", "citation"]):
        return "rag"
    if any(token in goal for token in ["abstain", "abstention", "selective", "deferral"]):
        return "abstention"
    if any(token in goal for token in ["agent", "tool", "workflow", "trace"]):
        return "agent"
    if any(token in goal for token in ["medical", "clinical", "segmentation", "imaging"]):
        return "medical"
    if any(token in goal for token in ["graph", "fraud", "node", "edge"]):
        return "graph_fraud"
    if any(token in goal for token in ["code", "programming", "tests", "pass@k"]):
        return "code"
    if any(token in goal for token in ["safety", "policy", "refusal", "unsafe"]):
        return "safety"
    if any(token in goal for token in ["image", "ocr", "chart", "video", "audio", "multimodal"]):
        return "multimodal"
    return "general"


def _benchmark_types(domain: str) -> list[str]:
    mapping = {
        "rag": ["evidence-grounded QA", "citation faithfulness", "answerable/unanswerable QA"],
        "abstention": ["selective prediction", "risk-coverage", "deferral utility"],
        "agent": ["tool-use traces", "replayable environments", "step-budget tasks"],
        "medical": ["site-stratified clinical QA", "segmentation with utility labels"],
        "graph_fraud": ["temporal graph splits", "fraud detection with precision@k"],
        "code": ["locked-dependency coding tasks", "hidden-test suites", "flaky-test screens"],
        "safety": ["policy-versioned safety tasks", "multi-turn refusal calibration"],
        "multimodal": ["image QA", "OCR/chart QA", "caption-only baseline tasks"],
    }
    return mapping.get(domain, ["construct-aligned local benchmark", "human-validated subset"])


def _minimum_diagnostics(domain: str) -> list[str]:
    common = [
        "provenance completeness",
        "shallow baselines",
        "prompt/scorer sensitivity",
        "reliability with uncertainty",
        "item-level forensics",
    ]
    domain_specific = {
        "rag": ["context removed", "evidence shuffled", "citation support checks"],
        "abstention": ["risk-coverage", "appropriate abstention", "deferral utility"],
        "agent": ["replay stability", "tool perturbation", "invalid call rate"],
        "medical": ["site-stratified performance", "severity-weighted scoring"],
        "graph_fraud": ["temporal split integrity", "degree-only baseline"],
        "code": ["test strength report", "dependency lock check", "flaky reruns"],
        "safety": ["paraphrase sensitivity", "rubric/judge sensitivity"],
        "multimodal": ["text-only baseline", "image removed", "crop/resolution sensitivity"],
    }
    return common + domain_specific.get(domain, [])


def _threats(domain: str) -> list[str]:
    common = ["construct mismatch", "shortcut artifacts", "scoring ambiguity", "coverage gaps"]
    domain_specific = {
        "rag": ["retrieval leakage", "unsupported citations", "faithfulness/helpfulness conflict"],
        "abstention": ["confidence miscalibration", "inappropriate refusal", "coverage gaming"],
        "agent": ["environment stochasticity", "hidden state leakage", "reward hacking"],
        "medical": ["label ambiguity", "site shift", "FP/FN asymmetry"],
        "graph_fraud": ["temporal leakage", "transductive leakage", "degree artifacts"],
        "code": ["GitHub overlap", "weak hidden tests", "package/version sensitivity"],
        "safety": ["policy staleness", "judge bias", "false safe/unsafe labels"],
        "multimodal": ["text leakage", "OCR shortcuts", "resolution sensitivity"],
    }
    return common + domain_specific.get(domain, [])


def _safe_claims(domain: str) -> list[str]:
    return [
        f"Evidence is consistent with the benchmark measuring aspects of {domain} under the audited protocol.",
        "The reported diagnostics identify possible validity threats and missing-evidence areas.",
        "Ranking interpretations are conditional on the scorer, model panel, and diagnostics run.",
    ]


def _needed_evidence(domain: str) -> list[str]:
    evidence = [
        "construct specification",
        "item provenance and split metadata",
        "scoring rules and extraction policy",
        "response matrices or local model outputs",
        "human validation plan for open-ended labels",
    ]
    if domain == "rag":
        evidence.extend(["support spans", "source documents", "unanswerable labels"])
    elif domain == "code":
        evidence.extend(["dependency lock files", "hidden-test strength report"])
    elif domain == "safety":
        evidence.extend(["policy version", "judge rubric version"])
    return evidence
