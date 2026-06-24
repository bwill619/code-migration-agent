from src.agents.state import MigrationState
from src.utils.ast_helpers import analyze_source_code

def parser_node(state: MigrationState) -> MigrationState:
    """
    LangGraph Agent Node: Inspects the incoming legacy code string and populates the graph state with detected anti-patterns.
    """
    print(f"\n--- [AGENT: PARSER] Analyzing structural patterns in {state['file_path']} ---")

    #Run the AST analysis helper
    analysis_results = analyze_source_code(state['legacy_code'])

    #Update local list of patterns to match state schema
    anti_patterns = analysis_results["anti_patterns"]

    #Catch intial code format errors
    if analysis_results["error"]:
        anti_patterns.append(analysis_results["error"])
    
    print(f"[PARSER SUCCESS] Identified {len(anti_patterns)} migration blocking patterns.")

    #Return updated state dictionary keys
    return {
        **state,
        "detected_anti_patterns": anti_patterns
    }