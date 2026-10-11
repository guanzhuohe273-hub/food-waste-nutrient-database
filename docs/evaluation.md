# Evaluation lineage

The MSc dissertation used frozen canonical, robustness and security suites. The formal scores below are preserved as historical results and are not retrospectively tuned.

- Deterministic canonical exact: **40/40 (100.0%)**
- Guarded GPT-5-mini canonical exact: **29/40 (72.5%)**
- Deterministic robustness exact: **21/40 (52.5%)**
- Guarded GPT-5-mini robustness exact: **21/40 (52.5%)**
- Guarded LLM execution: **80/80**
- Offline SQL safety suite: **26/26**

The portfolio extension targets failure classes identified by the dissertation: terminology normalization, target/response disambiguation, measurement-basis/schema mapping, and routing between deterministic and flexible query paths.

`scripts/evaluate_known_failures.py` is deliberately a **post-hoc known-failure regression**. It is not held-out evidence and must not be reported as new generalization accuracy.
