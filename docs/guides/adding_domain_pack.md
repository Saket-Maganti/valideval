# Adding a Domain Pack

Domain packs organize domain-specific threats, diagnostics, report sections, and repair policies.

Use this interface:

```python
class DomainPack:
    domain_id: str
    supported_item_types: list[str]
    threat_library: list[ThreatSpec]
    diagnostics: list[DiagnosticFactory]
    report_sections: list[ReportSectionFactory]
    repair_policies: list[RepairPolicy]
```

Checklist:

- Define threat specs with description, diagnostic evidence, repair guidance, and limitations.
- Add lightweight schemas for domain metadata.
- Add smoke fixtures that require no heavy dependencies.
- Add docs that separate implemented diagnostics from scaffolds.
- Register the pack so `python3 -m valideval domain list` and `domain describe` expose it.

Domain packs must not imply that domain validity has been established. Missing metadata should appear as missing evidence, not as a passed check.
