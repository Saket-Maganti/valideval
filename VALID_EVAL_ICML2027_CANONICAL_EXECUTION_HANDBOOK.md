# ValidEval ICML 2027 Canonical Execution Handbook

## Canonical

V7.2.1 S1 execution is canonical at `valideval-v7.2.1-icml2027-kaggle-s1-ready`. Resolve the tag dynamically; never paste an intermediate SHA into execution instructions.

## Historical

V5, V6, V7, V7.1, and V7.2 are historical for new execution. Their adapters remain explicit. V7's failed confirmatory result, V7.1's conservative baseline, and V7.2's generic policy result are frozen.

## Exploratory

V8 is exploratory development only and has no confirmatory authorization.

## What to run next

Check out valideval-v7.2.1-icml2027-kaggle-s1-ready and run kaggle_icml2027/00_v7_2_t4x2_preflight.ipynb on Kaggle with two T4 GPUs.

## Stage semantics

S1 validates engineering execution. S2 estimates runtime and pilot distributions. S3 requires a post-S2 design decision before scientific execution. S4 is optional and requires accepted S3 plus marginal-value justification. None of these stages automatically licenses a validity claim.

## Online, offline, and cache contract

The initial S1 smoke requires Internet to resolve the five models and three datasets at exact revisions. The declared model cache is 20,129,278,931 bytes; production preflight adds 7 GiB of free-disk margin. Reuse one cache across all three benchmark notebooks. Resume may use a complete exact-revision cache offline, but it must block rather than fetch or substitute an unpinned revision. Clear the cache only after the three validated ZIPs are safely downloaded.
