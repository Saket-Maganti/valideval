# Decoupled Synthetic Reviewer Audit Checklist

- Confirm hidden labels are unavailable to models.
- Confirm fixed readouts do not branch on flaw family names.
- Confirm outputs are marked `RESULT_REQUIRED` before execution.
- Confirm `paper evidence` remains false until real run artifacts are validated.
