# Security model

The optional LLM is not trusted with database authority.

Generated SQL must pass a local guard before execution:

- one read-only SELECT/WITH statement only;
- forbidden write/DDL/PRAGMA operations are rejected;
- referenced database objects must be allow-listed;
- SQLite is opened in read-only mode;
- a SQLite authorizer denies mutation-related actions;
- a progress handler limits query work;
- result rows are capped.

The execution guard protects the database boundary. It does **not** guarantee that a syntactically safe query is semantically correct, so evidence provenance and benchmark analysis remain part of the system design.

No API keys are committed to the repository. The deterministic and local evidence-retrieval paths work without an external LLM service.
