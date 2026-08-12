# ValidEval V7.1 Compute Optimization

Status: `COMPUTE_OPTIMIZATION_BLOCKED_PENDING_S2`.

The optimizer minimizes estimated T4 hours subject to target power and candidate design constraints,
but it requires measured accepted examples per second. No accepted S1/S2 T4 throughput artifact is
present. V7 planning ranges are intentionally not substituted for real measurements, so
`selected_design` is null.

Exact next input: an accepted S2 measurement artifact containing
`accepted_examples_per_second`, after which the optimizer can compare model, family, item, and
benchmark designs against the 0.80 target.
