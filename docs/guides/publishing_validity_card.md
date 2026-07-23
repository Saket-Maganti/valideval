# Publishing a Validity Card

Generate a card from existing artifacts:

```bash
python3 -m valideval card render --benchmark toy_mcq --panel mock
```

For local quickstart:

```bash
python3 -m valideval quickstart-audit --items items.jsonl --benchmark-card benchmark_card.md
```

Before publishing, include:

- Construct and intended-use statement.
- Diagnostics run and diagnostics not run.
- Dataset/config/scorer/prompt/diagnostic hashes.
- Known threats, warnings, and limitations.
- Reproduction commands.

Do not publish a validity card as a proof of benchmark validity. It is a structured evidence profile under the documented protocol.
