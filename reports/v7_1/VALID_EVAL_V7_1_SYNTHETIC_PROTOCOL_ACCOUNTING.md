# ValidEval V7.1 Synthetic Protocol Accounting

Primary status: `V7_SYNTHETIC_PRIMARY_GRID_FAILED_AND_PRESERVED`.

The frozen V7 primary grid and its failed acceptance decision were not rerun, overwritten, or
reinterpreted. V7.1 contains a new versioned control-completion module and config. Those outputs are
control observations, not a second attempt at V7 confirmation and not a license for a global
diagnostic-validity claim.

V7.1 metric code is deterministic under row reordering and ties. Precision-recall area advances at
complete equal-score groups. Precision@k reports the expected precision under random selection at a
boundary tie instead of depending on input order.

Every control row records study ID, seed, generator family, prevalence, tie policy, omitted
component where relevant, dependence setting, and the boundary
`CONTROL_OBSERVATION_NOT_CONFIRMATORY_SUCCESS_GATE`.
