from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Any


def reference_mmlu_parse(raw_output: str) -> str | None:
    text = str(raw_output).strip()
    compact = re.sub(r"[\s.!,:;()\[\]{}]+", "", text).upper()
    if compact in {"A", "B", "C", "D"}:
        return compact
    matches = re.findall(
        r"(?:final\s+answer|answer)\s*(?:is|:)\s*[\(\[]?([A-D])[\)\]]?(?![A-Za-z])",
        text,
        flags=re.I,
    )
    unique = {match.upper() for match in matches}
    return next(iter(unique)) if len(unique) == 1 else None


def reference_numeric_normalize(value: Any) -> str:
    text = str(value).strip().replace(",", "")
    text = re.sub(r"^[\$€£₹]\s*", "", text)
    if "/" in text:
        parts = [part.strip() for part in text.split("/")]
        if len(parts) != 2:
            raise ValueError("invalid fraction")
        try:
            value_fraction = Fraction(Decimal(parts[0])) / Fraction(Decimal(parts[1]))
        except (InvalidOperation, ValueError, ZeroDivisionError) as exc:
            raise ValueError("invalid fraction") from exc
        return f"{value_fraction.numerator}/{value_fraction.denominator}"
    try:
        decimal = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError("invalid number") from exc
    if not decimal.is_finite():
        raise ValueError("number must be finite")
    normalized = format(decimal.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return "0" if normalized in {"-0", "+0", ""} else normalized


def reference_gsm8k_parse(raw_output: str) -> str | None:
    text = str(raw_output).strip()
    if not text:
        return None
    matches = re.findall(r"(?:####|final\s+answer\s*(?:is|=|:)?)\s*([^\n]+)", text, flags=re.I)
    candidate = matches[-1].strip() if matches else text
    candidate = re.sub(r"^[\s$€£₹]+|[\s.!]+$", "", candidate)
    try:
        return reference_numeric_normalize(candidate)
    except ValueError:
        return None


def reference_bbh_parse(raw_output: str, task_kind: str) -> str | None:
    text = str(raw_output).strip()
    if not text:
        return None
    matches = re.findall(r"(?:####|final\s+answer\s*(?:is|=|:)?)\s*(.+)", text, flags=re.I)
    candidate = matches[-1].strip().splitlines()[0] if matches else text
    if task_kind == "MULTIPLE_CHOICE":
        match = re.fullmatch(r"\s*\(?([A-Za-z])\)?[.!]?\s*", candidate)
        return f"({match.group(1).upper()})" if match else None
    if task_kind == "BOOLEAN":
        value = candidate.casefold().rstrip(".")
        if value in {"true", "yes"}:
            return "True"
        if value in {"false", "no"}:
            return "False"
        return None
    if task_kind == "NUMERIC":
        try:
            return reference_numeric_normalize(candidate)
        except ValueError:
            return None
    return re.sub(r"\s+", " ", candidate).strip().casefold().rstrip(".") or None
