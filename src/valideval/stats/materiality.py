from __future__ import annotations


def materiality_label(effect_size: float | None, *, threshold: float = 0.20) -> str:
    if effect_size is None:
        return "uncalibrated"
    if abs(float(effect_size)) >= threshold:
        return "practically_material"
    if abs(float(effect_size)) > 0:
        return "detectable_not_material"
    return "negligible"
