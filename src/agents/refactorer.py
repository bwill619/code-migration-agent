import os
from openai import OpenAI
from src.agents.state import MigrationState


openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    
    # Track iteration count to prevent budget runaway loops
    current_iterations = state.get("iteration_count", 0) + 1
    
    # Format structural prompt
    prompt = generate_upgrade_prompt(
        legacy_code=state["legacy_code"],
        anti_patterns=state.get("detected_anti_patterns", []),
        docs=state.get("retrieved_docs", []),
        validation_errors=state.get("validation_errors")
    )
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        raw_content = response.choices[0].message.content
        
        # Extract purely the Python code from the LLM code block wrapper
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
