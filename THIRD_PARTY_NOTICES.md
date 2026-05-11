# Third-Party Notices

This file records third-party open-source components used by optional Agent-ValueBench workflows.

## Harbor

- **Upstream:** https://github.com/harbor-framework/harbor
- **Recommended revision:** `0533a59c41ce435d9e59ff8c82da67f6e5b6edc7`
- **License:** Apache License 2.0
- **Local checkout path after setup:** `HarnessEval/harbor/`

Harbor supports optional Codex and Claude Code harness experiments in `HarnessEval`. It is not vendored in this repository. Users clone Harbor from upstream into `HarnessEval/harbor/` during setup; its license and README are provided by that upstream checkout.

If you use the Harbor-based experiments in academic work, please also cite
Harbor:

```bibtex
@software{Harbor_Framework,
author = {{Harbor Framework Team}},
month = jan,
title = {{Harbor: A framework for evaluating and optimizing agents and models in container environments}},
url = {https://github.com/harbor-framework/harbor},
year = {2026}
}
```
