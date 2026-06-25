import os
from src.agents.state import MigrationState


def _call_llm(prompt: str) -> str:
    """Tries OpenAI gpt-4o first; falls back to Anthropic claude if key unavailable."""
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            response = OpenAI(api_key=openai_key).chat.completions.create(
                model=os.getenv("LLM_MODEL", "gpt-4o"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            if any(code in str(e) for code in ("insufficient_quota", "invalid_api_key", "429", "401")):
                print("[REFACTORER] OpenAI key unavailable, falling back to Anthropic.")
            else:
                raise

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        import anthropic
        response = anthropic.Anthropic(api_key=anthropic_key).messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    raise RuntimeError("No LLM provider available. Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env.")


def generate_upgrade_prompt(legacy_code: str, anti_patterns: list, docs: list, validation_errors: str = None) -> str:
    """Constructs a densely grounded engineering prompt for codebase refactoring."""
    prompt = f"""You are an elite Staff Software Engineer specializing in Python migration pipelines.
Your task is to refactor a legacy Python code file into an optimized, asynchronous file using FastAPI and modern Python 3.12+ features.

### LEGACY SOURCE CODE:
```python
{legacy_code}
```

### DETECTED ANTI-PATTERNS TO RESOLVE:
{chr(10).join([f'- {p}' for p in anti_patterns]) if anti_patterns else '- General architecture overhaul to async FastAPI.'}

### GROUNDING DOCUMENTATION / MIGRATION RULES:
{chr(10).join([f'--- DOCUMENT BLOCK ---\n{d}' for d in docs]) if docs else 'Apply general industry best practices for async Python and FastAPI structures.'}
"""

    if validation_errors:
        prompt += f"""
  IMPORTANT - PREVIOUS COMPILATION / RUNTIME ERRORS:
Your previous attempt generated the following test/runtime failures. Inspect this trace and correct it:
```text
{validation_errors}
```
"""

    prompt += """
### STRICT COMPLIANCE RULES:
1. Return ONLY valid, executable Python code.
2. Wrap your entire output in a single markdown code block: ```python ... ```
3. Ensure all synchronous IO blockages (like time.sleep or sync requests) are converted to their proper async equivalents.
4. Maintain all business logic, endpoint mappings, and variable integrity.
"""
    return prompt


def refactorer_node(state: MigrationState) -> MigrationState:
    """
    LangGraph Agent Node: Synthesizes input code and RAG context to
    generate modern, production-grade asynchronous code blocks.
    """
    print("\n--- [AGENT: REFACTORER] Synthesizing upgraded source code ---")

    current_iterations = state.get("iteration_count", 0) + 1

    prompt = generate_upgrade_prompt(
        legacy_code=state["legacy_code"],
        anti_patterns=state.get("detected_anti_patterns", []),
        docs=state.get("retrieved_docs", []),
        validation_errors=state.get("validation_errors")
    )

    try:
        raw_content = _call_llm(prompt)

        if "```python" in raw_content:
            refactored_code = raw_content.split("```python")[1].split("```")[0].strip()
        else:
            refactored_code = raw_content.strip()

        print("[REFACTORER SUCCESS] Generated modern codebase diff generation candidate.")

        return {
            **state,
            "refactored_code": refactored_code,
            "iteration_count": current_iterations
        }

    except Exception as e:
        print(f"[REFACTORER ERROR] Failed code generation execution: {e}")
        return {
            **state,
            "iteration_count": current_iterations
        }
