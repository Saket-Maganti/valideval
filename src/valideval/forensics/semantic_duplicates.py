from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from typing import Any

import numpy as np

from valideval.forensics.provenance import item_text
from valideval.forensics.report import risk_from_fraction, signal
from valideval.schemas import BenchmarkItem


def semantic_duplicate_report(
    items: list[BenchmarkItem],
    *,
    threshold: float = 0.85,
    min_token_length: int = 3,
) -> dict[str, Any]:
    if len(items) < 2:
        return signal(
            status="measured",
            risk_level="no local evidence found",
            metrics={
                "cluster_count": 0,
                "semantic_duplicate_fraction": 0.0,
                "clusters": [],
                "duplicate_item_ids": [],
                "method": "tfidf_cosine",
                "threshold": threshold,
            },
            warnings=["Fewer than two items; semantic duplicate scan skipped."],
        )

    texts = [item_text(item) for item in items]
    vectors = _tfidf_vectors(texts, min_token_length=min_token_length)
    clusters = _cluster_by_cosine(items, vectors, threshold=threshold)
    duplicate_ids = sorted({item_id for cluster in clusters for item_id in cluster[1:]})
    duplicate_fraction = len(duplicate_ids) / len(items) if items else 0.0
    return signal(
        status="measured",
        risk_level=risk_from_fraction(duplicate_fraction),
        metrics={
            "cluster_count": len(clusters),
            "semantic_duplicate_fraction": duplicate_fraction,
            "clusters": clusters,
            "duplicate_item_ids": duplicate_ids,
            "method": "tfidf_cosine",
            "threshold": threshold,
            "vocabulary_size": vectors.shape[1] if vectors.size else 0,
        },
        warnings=[
            "Semantic duplicate detection uses offline TF-IDF cosine similarity; "
            "paraphrases with low lexical overlap may be missed.",
            "This signal complements lexical duplicate checks; it does not prove contamination.",
        ],
    )


def _tokenize(text: str, *, min_token_length: int) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [token for token in tokens if len(token) >= min_token_length]


def _tfidf_vectors(texts: list[str], *, min_token_length: int) -> np.ndarray:
    tokenized = [_tokenize(text, min_token_length=min_token_length) for text in texts]
    document_frequency: Counter[str] = Counter()
    for tokens in tokenized:
        document_frequency.update(set(tokens))
    vocabulary = sorted(document_frequency)
    if not vocabulary:
        return np.zeros((len(texts), 0), dtype=float)

    index = {token: position for position, token in enumerate(vocabulary)}
    matrix = np.zeros((len(texts), len(vocabulary)), dtype=float)
    for row_index, tokens in enumerate(tokenized):
        counts = Counter(tokens)
        total = sum(counts.values()) or 1
        for token, count in counts.items():
            tf = count / total
            idf = math.log((1 + len(texts)) / (1 + document_frequency[token])) + 1.0
            matrix[row_index, index[token]] = tf * idf

    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def _cluster_by_cosine(
    items: list[BenchmarkItem],
    vectors: np.ndarray,
    *,
    threshold: float,
) -> list[list[str]]:
    if vectors.size == 0:
        return []

    parent = {item.item_id: item.item_id for item in items}

    def find(item_id: str) -> str:
        while parent[item_id] != item_id:
            parent[item_id] = parent[parent[item_id]]
            item_id = parent[item_id]
        return item_id

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for left_index in range(len(items)):
        for right_index in range(left_index + 1, len(items)):
            similarity = float(np.dot(vectors[left_index], vectors[right_index]))
            if similarity >= threshold:
                union(items[left_index].item_id, items[right_index].item_id)

    groups: dict[str, list[str]] = defaultdict(list)
    for item in items:
        groups[find(item.item_id)].append(item.item_id)
    return [sorted(group) for group in groups.values() if len(group) > 1]
