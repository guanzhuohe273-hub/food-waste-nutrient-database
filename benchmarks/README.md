# Historical dissertation evaluation

The MSc dissertation used frozen canonical, robustness and security suites.

Formal results:

- Deterministic canonical exact: **40/40 (100.0%)**
- Guarded GPT-5-mini canonical exact: **29/40 (72.5%)**
- Deterministic robustness exact: **21/40 (52.5%)**
- Guarded GPT-5-mini robustness exact: **21/40 (52.5%)**
- Guarded LLM execution: **80/80**
- Offline SQL-safety suite: **26/26**

These are historical dissertation results. The semantic normalizer and hybrid router in this repository are post-dissertation engineering extensions, so the historical scores are not relabelled as evaluation of the extension.

A future headline accuracy result should use a newly frozen benchmark created before further tuning.
