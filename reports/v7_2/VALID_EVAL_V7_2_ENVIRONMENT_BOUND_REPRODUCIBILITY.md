# Environment-Bound Reproducibility

Evidence identity comprises source commit, config hash, dependency-lock hash, platform metadata,
seed-manifest hash, and normalized-result hash. `replay/v7_2/ENVIRONMENT_IDENTITY.json` records the
identity. Exact replay is required within that frozen environment; identical hashes are not
promised across arbitrary NumPy/SciPy versions.
