# ValidEval V7.1 Canonical vs Deduplicated Estimands

MMLU status: `CANONICAL_AND_DEDUPLICATED_ESTIMANDS_READY`.

BBH status: `BLOCKED_PENDING_EXACT_STUDY_C_RESPONSE_MATRIX`.

The cached MMLU comparison uses 39 models and contrasts all 14,042 canonical items with the 14,015
items retained by the frozen validity-analysis manifest. Frozen global test-split row indices are
mapped to HELM source IDs through canonical subject offsets and within-subject numeric source order.

The winner and top five were unchanged. Both conditions licensed two simultaneous top-five models;
the canonical condition had 681 directional pairwise decisions and 50 abstentions, versus 681 and
49 for the deduplicated validity-analysis condition. The winner accuracy changed from 0.867611 to
0.867499.

The deduplicated result is always labeled a validity-analysis estimand and never canonical MMLU.
No BBH comparison was fabricated because the exact Study-C response matrix is unavailable.
