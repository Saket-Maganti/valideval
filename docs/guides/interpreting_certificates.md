# Interpreting Certificates

ValidEval certificates are evidence profiles / audit completeness profiles. They are not scalar validity scores or quality grades.

Profiles are based on available artifacts:

- insufficient_evidence: required audit artifacts are missing or too sparse.
- metadata_and_provenance_recorded: metadata, reproducible card, and basic provenance evidence are recorded.
- core_diagnostics_recorded: shortcut, item-quality, and reliability evidence are recorded.
- human_review_evidence_recorded: contamination/provenance plus human/judge validation evidence is recorded.
- external_validation_evidence_recorded: predictive/consequential validity or external replication evidence is recorded.

Missing evidence lowers audit completeness. It does not prove that a benchmark is bad. A complete profile also does not prove that the benchmark is valid for every use.

Report certificates with the card, manifest, diagnostics, and limitations.
