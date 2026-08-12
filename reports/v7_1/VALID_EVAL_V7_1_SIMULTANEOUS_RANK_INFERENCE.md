# ValidEval V7.1 Simultaneous Rank Inference

Status: `SIMULTANEOUS_RANK_INFERENCE_READY`.

The V7.1 method derives ranks jointly in every resampling draw and calibrates one critical maximum
absolute rank deviation across all models. Reported top-k licenses accept only interval type
`BOOTSTRAP_MAX_DEVIATION_SIMULTANEOUS`; marginal percentile intervals are emitted in a separate
artifact and cannot satisfy this gate.

Known-truth simulation used 200 datasets and 300 bootstrap draws per scenario for eight models and
four families. Joint coverage was 1.000 in the three non-tied scenarios and 0.985, 0.990, and 0.995
in the tied scenarios as family correlation varied over 0.0, 0.6, and 0.9. These observations are
conditional on this simulation family and are not a general coverage theorem.

Study H used 500 nested subject/item joint draws. The simultaneous critical rank deviation was 5;
the marginal intervals are intentionally not substituted for these confidence sets.
