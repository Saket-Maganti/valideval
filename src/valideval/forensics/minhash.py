from __future__ import annotations

import hashlib

from valideval.scoring.mcq_utils import tokenize


def minhash_signature(text: str, *, num_perm: int = 64) -> list[int]:
    tokens = set(tokenize(text))
    if not tokens:
        return [0] * num_perm
    signature = []
    for seed in range(num_perm):
        values = [
            int(
                hashlib.sha256(f"{seed}|{token}".encode()).hexdigest()[:16],
                16,
            )
            for token in tokens
        ]
        signature.append(min(values))
    return signature


def minhash_similarity(left: list[int], right: list[int]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(int(a == b) for a, b in zip(left, right, strict=True)) / len(left)
