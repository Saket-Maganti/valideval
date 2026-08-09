# ValidEval V7 Human Study Final Protocol

Gate: `HUMAN_CONFIRMATORY_PROTOCOL_READY`; human evidence: `NOT_EXECUTED`.

The protocol uses disjoint high, medium, low, and probability-control strata; deterministic
benchmark/subject balancing; a physically separate randomization key; positive and negative
controls; two or three annotators; a frozen issue taxonomy; nominal agreement metrics; specialist
adjudication; and raw-versus-adjudicated reporting. Annotators do not see diagnostic scores,
selection reasons, external labels, model identities, or response patterns where avoidable.

The primary endpoint is precision in the preregistered flagged stratum. Recall is not identifiable
from the stratified design and must not be claimed. At 300 annotations per stratum, the planning
95% precision interval around an assumed 0.70 precision is [0.646,
0.749]. These are planning assumptions, not labels.

V7 sampling is in `src/valideval/human/protocol_v7.py`; the audited V5 blinded packet, secure import,
agreement, and adjudication modules remain the execution path.
