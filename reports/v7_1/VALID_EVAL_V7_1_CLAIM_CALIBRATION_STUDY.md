# ValidEval V7.1 Claim-Policy Calibration Study

Status: `CLAIM_POLICY_CALIBRATION_READY`.

The known-truth CPU study compares naive point decisions, confidence-interval-only decisions,
FDR-only decisions, and full ValidEval licensing over 864 cells. It varies true effect, raw and
effective N, family dependence, multiplicity, and transport heterogeneity with 200 replicates per
cell. Coverage, false-license rate, false-block rate, power, regret, and Monte Carlo SE are retained.

Across the grid, mean false-license rates were 0.395 for naive decisions, 0.017 for CI-only, 0.009
for FDR-only, and 0 for full licensing. Full licensing also had zero simulated power in this grid
because its decision-regret and evidence gates were deliberately stringent. This is evidence of a
conservative operating point, not proof that the policy is optimal. Calibration is conditional on
the declared simulation distributions.

The selective-decision table is labeled `EMPIRICAL_NOT_THEOREM`; it does not claim a mathematical
guarantee.
