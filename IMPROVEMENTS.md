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
- [x] Expand `knowledge_base.json` with rules matching new parser patterns (8 rules total: Blueprint→APIRouter, requests→httpx, jsonify→Pydantic, lifecycle hooks, error handlers)
- [x] Respect `LLM_PROVIDER` env var in refactorer — setting `LLM_PROVIDER=anthropic` now routes directly to Anthropic without attempting OpenAI

## Tier 3: Validation Depth
- [x] Strengthen validator beyond `py_compile` — two-stage check: syntax (py_compile) then AST quality scan (FastAPI imported, Flask gone, no time.sleep/requests remaining, route handlers are async def)

## Tier 4: Roadmap
- [x] Multi-file support — `--input` now accepts a directory; discovers all `.py` files and writes migrated output to a parallel directory structure via `--output`
- [x] Evaluation reporting — `--report` writes a JSON report per run tracking patterns detected, docs retrieved, iterations, pass/fail per file, and aggregate pass rate and avg iterations
