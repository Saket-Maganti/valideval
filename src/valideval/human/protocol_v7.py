from __future__ import annotations

from collections import defaultdict, deque

import numpy as np
import pandas as pd


def stratified_candidate_sample(
    candidates: pd.DataFrame,
    *,
    per_stratum: int,
    seed: int = 2027,
) -> pd.DataFrame:
    """Freeze high/medium/low diagnostic strata plus disjoint random controls.

    Selection balances benchmark/subject cells by round-robin. Scores and stratum
    labels are private metadata that the blinded packet builder must remove.
    """

    required = {"item_id", "diagnostic_score", "subject", "benchmark"}
    if not required.issubset(candidates.columns):
        raise ValueError(
            f"human candidates are missing {sorted(required - set(candidates.columns))}"
        )
    if per_stratum <= 0:
        raise ValueError("per_stratum must be positive")
    frame = candidates.copy()
    if frame["item_id"].astype(str).duplicated().any():
        raise ValueError("human candidates contain duplicate item IDs")
    scores = frame["diagnostic_score"].to_numpy(dtype=float)
    if np.any(~np.isfinite(scores)):
        raise ValueError("diagnostic scores must be finite")
    low, medium_low, medium_high, high = np.quantile(scores, [0.25, 0.375, 0.625, 0.75])
    pools = {
        "high_diagnostic": frame[frame["diagnostic_score"] >= high],
        "medium_diagnostic": frame[
            frame["diagnostic_score"].between(medium_low, medium_high, inclusive="both")
        ],
        "low_diagnostic": frame[frame["diagnostic_score"] <= low],
    }
    selected: list[pd.DataFrame] = []
    selected_ids: set[str] = set()
    for offset, (stratum, pool) in enumerate(pools.items()):
        draw = _balanced_draw(pool, per_stratum, seed + offset)
        draw = draw.assign(diagnostic_stratum=stratum, selection_reason=stratum)
        selected.append(draw)
        selected_ids.update(draw["item_id"].astype(str))
    controls = frame[~frame["item_id"].astype(str).isin(selected_ids)]
    control_draw = _balanced_draw(controls, per_stratum, seed + 100)
    selected.append(
        control_draw.assign(
            diagnostic_stratum="random_control",
            selection_reason="probability_control",
        )
    )
    output = pd.concat(selected, ignore_index=True)
    output["sampling_seed"] = seed
    output["inclusion_role"] = np.where(
        output["diagnostic_stratum"] == "random_control", "control", "flagged_stratum"
    )
    return output


def _balanced_draw(frame: pd.DataFrame, count: int, seed: int) -> pd.DataFrame:
    if len(frame) < count:
        raise ValueError(f"stratum contains {len(frame)} candidates but requires {count}")
    shuffled = frame.sample(frac=1.0, random_state=seed)
    groups: dict[tuple[str, str], deque[int]] = defaultdict(deque)
    for index, row in shuffled.iterrows():
        groups[(str(row["benchmark"]), str(row["subject"]))].append(index)
    ordered_keys = sorted(groups)
    chosen: list[int] = []
    while len(chosen) < count:
        progressed = False
        for key in ordered_keys:
            if groups[key]:
                chosen.append(groups[key].popleft())
                progressed = True
                if len(chosen) == count:
                    break
        if not progressed:
            break
    if len(chosen) != count:
        raise ValueError("balanced sampler exhausted candidates unexpectedly")
    return frame.loc[chosen].copy()
