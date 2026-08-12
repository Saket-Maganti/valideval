from __future__ import annotations

import json

from valideval.scoring.extraction_stress_v7_2_1 import run_extraction_stress

if __name__ == "__main__":
    print(
        json.dumps(
            run_extraction_stress("results/final_cpu_maxout/extraction"),
            indent=2,
            sort_keys=True,
        )
    )
