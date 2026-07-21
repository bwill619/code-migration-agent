# Project Improvements Checklist

## Tier 1: Quick Wins
- [x] Add `--output` flag to save migrated code to a file instead of printing to stdout
- [x] Delete `src/database/qdrant_client.py` (dead code from Docker-based setup)
- [x] Fix typo `LegacacyCodeAnalyzer` → `LegacyCodeAnalyzer` and deduplicate visitor methods
- [x] Move knowledge base rules to `knowledge_base.json` (no code changes needed to add rules)

## Tier 2: Core Capability Gaps
- [x] Expand AST parser to catch more anti-patterns:
  - `from flask import ...` / `from flask import Blueprint`
  - `requests.get/post/put/delete/patch()` sync HTTP calls
  - `jsonify()` usage
  - `@app.before_request`, `@app.after_request`, `@app.errorhandler` hooks
- [ ] Expand `knowledge_base.json` with rules matching new parser patterns
- [ ] Respect `LLM_PROVIDER` env var in refactorer (currently always tries OpenAI first)

## Tier 3: Validation Depth
- [ ] Strengthen validator beyond `py_compile` — check that async/await patterns are present in output and that expected FastAPI imports exist

## Tier 4: Roadmap
- [ ] Multi-file support — handle projects with cross-file imports and shared models
- [ ] Ragas evaluation — track retrieval precision and code faithfulness across a test suite
