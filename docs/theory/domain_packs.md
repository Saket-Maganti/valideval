# Domain Packs

Domain packs let `valideval` keep core validity logic separate from domain-specific threats. A pack defines supported item types, a threat library, diagnostic factories, report sections, and repair policies.

The interface is:

```python
class DomainPack:
    domain_id: str
    supported_item_types: list[str]
    threat_library: list[ThreatSpec]
    diagnostics: list[DiagnosticFactory]
    report_sections: list[ReportSectionFactory]
    repair_policies: list[RepairPolicy]
```

## Commands

```bash
python3 -m valideval domain list
python3 -m valideval domain describe rag
python3 -m valideval audit --benchmark toy_mcq --panel mock --domain rag
python3 -m valideval audit --benchmark toy_mcq --panel mock --domain abstention
python3 -m valideval report --benchmark toy_mcq --panel mock
```

`audit --domain rag` adds the RAG pack diagnostics. It does not replace the need to report assumptions, missing metadata, and limitations.

## Working Offline Packs

RAG:

- context removed
- evidence shuffled
- distractor injected
- support-span interface
- citation checks
- unanswerable refusal metadata
- context reliance
- evidence-position sensitivity

Abstention:

- selective risk
- coverage
- risk-coverage AUC
- appropriate abstention
- inappropriate refusal
- confidence-validity correlation when confidence/logprobs exist
- uncertainty under paraphrase when perturbation matrices exist
- deferral utility

## Scaffold Packs

Agent, medical/segmentation, graph/fraud, code, safety, and multimodal packs currently provide schema extensions, threat specs, repair policy definitions, docs, and fixture smoke tests. They do not claim full empirical diagnostic coverage yet.

## Threat Library

Threat specs live in `src/valideval/domains/threats.json`. Each record includes:

- `name`
- `domain`
- `description`
- `diagnostic`
- `evidence`
- `repair`
- `limitations`

The threat library is a map of possible validity threats. It is not evidence that the threat is present in a benchmark.

## Interpretation

Domain-pack diagnostics are conditional evidence under local metadata, cached matrices, and toy fixtures. Unavailable signals should be reported as missing evidence, not as clean bills of health. Report cards include domain pack sections separately and do not collapse them into a single validity score.
