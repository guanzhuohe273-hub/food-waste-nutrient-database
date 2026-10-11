# Limitations

- The evidence base covers six source studies and is not a comprehensive survey of food-waste valorisation.
- The 408 rows are measurements, not 408 statistically independent ML training cases.
- The deterministic path has a controlled-language envelope; normalization improves known variants but does not make it open-domain.
- The optional LLM path can still produce semantically wrong but syntactically valid SQL. The guard protects the execution boundary, not semantic correctness.
- The local retrieval fallback is intentionally lightweight and is not an embedding benchmark.
- The known-failure regression is post-hoc and not held out. A new headline accuracy number should only be reported after freezing a new benchmark before further tuning.
