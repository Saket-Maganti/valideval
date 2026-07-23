# Plugin Package Creation

Third-party packages can register loaders, model runners, scorers, extractors, diagnostics, report sections, repair policies, domain packs, and visualizations.

Available decorators:

- `@valideval.benchmark_loader("name")`
- `@valideval.model_runner("name")`
- `@valideval.scorer("name")`
- `@valideval.extractor("name")`
- `@valideval.diagnostic("name")`
- `@valideval.report_section("name")`
- `@valideval.repair_policy("name")`
- `@valideval.domain_pack("name")`
- `@valideval.visualization("name")`

Example:

```python
import valideval


@valideval.diagnostic("source_license_check")
class SourceLicenseCheck:
    ...
```

Users can inspect registered plugins:

```bash
python3 -m valideval plugins list
python3 -m valideval plugins list --kind diagnostic
```

Plugin packages should keep optional dependencies optional, document artifact formats, and avoid required paid APIs.
