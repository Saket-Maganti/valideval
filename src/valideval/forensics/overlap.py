from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from valideval.benchmarks.base import Benchmark
from valideval.forensics.provenance import item_text
from valideval.forensics.report import risk_from_fraction, signal, status_for_corpus
from valideval.schemas import BenchmarkItem
from valideval.scoring.mcq_utils import correct_choice_text, tokenize

SUPPORTED_CORPUS_EXTENSIONS = {".txt", ".md", ".jsonl", ".json", ".csv"}


@dataclass(frozen=True)
class CorpusDocument:
    doc_id: str
    path: str
    text: str


def load_local_corpus(path: str | Path) -> list[CorpusDocument]:
    root = Path(path)
    if not root.exists():
        return []
    files = [root] if root.is_file() else sorted(root.rglob("*"))
    docs: list[CorpusDocument] = []
    for file in files:
        if not file.is_file() or file.suffix.lower() not in SUPPORTED_CORPUS_EXTENSIONS:
            continue
        docs.extend(_read_file_documents(file))
    return docs


def scan_corpus_overlap(
    benchmark: Benchmark,
    corpus_path: str | Path | None,
    *,
    ngram_n: int = 5,
) -> dict[str, Any]:
    items = benchmark.load_items()
    if corpus_path is None:
        return signal(
            status="unavailable",
            risk_level="unknown/unmeasured",
            warnings=["No local corpus was supplied; external overlap was not measured."],
            limitations=["Absence of a corpus is not evidence of cleanliness."],
        )
    docs = load_local_corpus(corpus_path)
    if not docs:
        return signal(
            status=status_for_corpus(0),
            risk_level="insufficient corpus",
            metrics={"corpus_path": str(corpus_path), "documents_searched": 0},
            warnings=["No supported local corpus documents were found."],
        )

    per_item = {item.item_id: _item_overlap(item, docs, ngram_n=ngram_n) for item in items}
    exact_matches = [item_id for item_id, metrics in per_item.items() if metrics["exact_match"]]
    question_matches = [
        item_id for item_id, metrics in per_item.items() if metrics["question_match"]
    ]
    suspicious = [
        item_id for item_id, metrics in per_item.items() if metrics["item_suspiciousness"] >= 0.5
    ]
    overlap_fraction = len(suspicious) / len(items) if items else 0.0
    return signal(
        status="measured",
        risk_level=risk_from_fraction(overlap_fraction),
        metrics={
            "corpus_path": str(corpus_path),
            "documents_searched": len(docs),
            "exact_match_rate": len(exact_matches) / len(items) if items else 0.0,
            "question_match_rate": len(question_matches) / len(items) if items else 0.0,
            "suspicious_item_rate": overlap_fraction,
            "suspicious_items": suspicious,
            "per_item": per_item,
        },
        warnings=[
            "Corpus overlap is corpus-dependent evidence, not proof of contamination.",
            "No local overlap is not proof of cleanliness.",
        ],
    )


def _item_overlap(
    item: BenchmarkItem,
    docs: list[CorpusDocument],
    *,
    ngram_n: int,
) -> dict[str, Any]:
    item_full_text = _normalize(item_text(item))
    question = _normalize(item.prompt)
    answers = _candidate_answer_texts(item)
    best: dict[str, Any] = {
        "doc_id": None,
        "path": None,
        "ngram_overlap": 0.0,
        "longest_common_substring": 0,
    }
    exact_match = False
    question_match = False
    answer_match = False
    for doc in docs:
        doc_text = _normalize(doc.text)
        exact_match = exact_match or bool(item_full_text and item_full_text in doc_text)
        question_match = question_match or bool(question and question in doc_text)
        answer_match = answer_match or any(_contains_answer(doc_text, answer) for answer in answers)
        ngram_overlap = _ngram_overlap(question, doc_text, n=ngram_n)
        lcs = _longest_common_substring_len(question, doc_text)
        score = max(ngram_overlap, min(lcs / max(len(question), 1), 1.0))
        if score > max(
            best["ngram_overlap"], best["longest_common_substring"] / max(len(question), 1)
        ):
            best = {
                "doc_id": doc.doc_id,
                "path": doc.path,
                "ngram_overlap": ngram_overlap,
                "longest_common_substring": lcs,
            }
    suspiciousness = max(
        1.0 if exact_match else 0.0,
        0.9 if question_match else 0.0,
        0.4 if answer_match else 0.0,
        float(best["ngram_overlap"]),
        min(float(best["longest_common_substring"]) / max(len(question), 1), 1.0),
    )
    return {
        "exact_match": exact_match,
        "question_match": question_match,
        "answer_match": answer_match,
        "max_ngram_overlap": best["ngram_overlap"],
        "longest_common_substring": best["longest_common_substring"],
        "top_matching_doc": {"doc_id": best["doc_id"], "path": best["path"]},
        "item_suspiciousness": suspiciousness,
        "risk_level": _item_risk_level(suspiciousness),
    }


def _read_file_documents(path: Path) -> list[CorpusDocument]:
    suffix = path.suffix.lower()
    try:
        if suffix in {".txt", ".md"}:
            return [CorpusDocument(path.name, str(path), path.read_text(encoding="utf-8"))]
        if suffix == ".jsonl":
            docs = []
            for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    payload = {"text": line}
                docs.append(
                    CorpusDocument(
                        f"{path.name}:{idx}",
                        str(path),
                        _payload_text(payload),
                    )
                )
            return docs
        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return [
                    CorpusDocument(f"{path.name}:{idx}", str(path), _payload_text(item))
                    for idx, item in enumerate(payload)
                ]
            return [CorpusDocument(path.name, str(path), _payload_text(payload))]
        if suffix == ".csv":
            docs = []
            with path.open("r", encoding="utf-8", newline="") as handle:
                for idx, row in enumerate(csv.DictReader(handle)):
                    docs.append(
                        CorpusDocument(
                            f"{path.name}:{idx}",
                            str(path),
                            " ".join(str(value) for value in row.values() if value is not None),
                        )
                    )
            return docs
    except UnicodeDecodeError:
        return []
    return []


def _payload_text(payload: Any) -> str:
    if isinstance(payload, dict):
        fields = [
            payload.get(key)
            for key in [
                "text",
                "prompt",
                "question",
                "context",
                "answer",
                "choices",
                "abstract",
                "description",
            ]
        ]
        return " ".join(_payload_text(field) for field in fields if field is not None)
    if isinstance(payload, list):
        return " ".join(_payload_text(item) for item in payload)
    return str(payload)


def _candidate_answer_texts(item: BenchmarkItem) -> list[str]:
    values = []
    choice_text = correct_choice_text(item)
    if choice_text:
        values.append(choice_text)
    raw_answers = item.answer if isinstance(item.answer, list) else [item.answer]
    for answer in raw_answers:
        value = str(answer).strip()
        if item.choices and value.upper() in {"A", "B", "C", "D"}:
            continue
        values.append(value)
    return [_normalize(value) for value in values if _normalize(value)]


def _contains_answer(doc_text: str, answer: str) -> bool:
    if not answer:
        return False
    if len(answer) <= 2:
        return bool(re.search(rf"\b{re.escape(answer)}\b", doc_text))
    return answer in doc_text


def _item_risk_level(suspiciousness: float) -> str:
    if suspiciousness >= 0.75:
        return "high local evidence"
    if suspiciousness >= 0.50:
        return "moderate local evidence"
    if suspiciousness >= 0.25:
        return "low local evidence"
    return "no local evidence found"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _ngrams(text: str, n: int) -> set[tuple[str, ...]]:
    tokens = tokenize(text)
    if len(tokens) < n:
        return {tuple(tokens)} if tokens else set()
    return {tuple(tokens[index : index + n]) for index in range(len(tokens) - n + 1)}


def _ngram_overlap(left: str, right: str, *, n: int) -> float:
    left_ngrams = _ngrams(left, n)
    right_ngrams = _ngrams(right, n)
    if not left_ngrams:
        return 0.0
    return len(left_ngrams & right_ngrams) / len(left_ngrams)


def _longest_common_substring_len(left: str, right: str) -> int:
    if not left or not right:
        return 0
    previous = [0] * (len(right) + 1)
    best = 0
    for left_char in left:
        current = [0]
        for idx, right_char in enumerate(right, start=1):
            value = previous[idx - 1] + 1 if left_char == right_char else 0
            current.append(value)
            best = max(best, value)
        previous = current
    return best
