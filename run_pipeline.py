import os
import argparse
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

# Load environment configs early
load_dotenv()

from src.agents.state import MigrationState
from src.agents.parser import parser_node
from src.agents.retriever import retriever_node
from src.agents.refactorer import refactorer_node
from src.agents.validator import validator_node

def route_validation_results(state: MigrationState):
    """
    Conditional Router Edge: Directs flow to the END state on success,
    or loops back to self-correct up to a maximum threshold.
    """
    errors = state.get("validation_errors")
    iterations = state.get("iteration_count", 0)
    
    if errors:
        if iterations >= 3:
            print(f"\n [GRAPH LIMIT REACHED] Failed to self-correct after {iterations} attempts. Halting.")
            return END
        print(f"\n[GRAPH ROUTER] Refactoring failed validation checkpoint. Routing back for Pass #{iterations + 1}.")
        return "retriever_agent"
        
    print("\n[GRAPH ROUTER] Validation completely clean. Finalizing pipeline extraction.")
    return END

def build_migration_graph():
    """Compiles individual discrete agent nodes into a strict LangGraph state machine."""
    workflow = StateGraph(MigrationState)
    
    # Register individual worker nodes
    workflow.add_node("parser_agent", parser_node)
    workflow.add_node("retriever_agent", retriever_node)
    workflow.add_node("refactorer_agent", refactorer_node)
    workflow.add_node("validator_agent", validator_node)
    
    # Establish topological execution paths
    workflow.set_entry_point("parser_agent")
    workflow.add_edge("parser_agent", "retriever_agent")
    workflow.add_edge("retriever_agent", "refactorer_agent")
    workflow.add_edge("refactorer_agent", "validator_agent")
    
    # Inject active routing edge decision logic based on automated test runs
    workflow.add_conditional_edges(
        "validator_agent",
        route_validation_results,
        {
            "retriever_agent": "retriever_agent",
            END: END
        }
    )
    
    return workflow.compile()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Autonomous Code Migration Multi-Agent RAG Pipeline.")
    parser.add_argument("--input", required=True, help="Path to the legacy Python code file.")
    parser.add_argument("--output", required=False, help="Path to write the migrated output file. Prints to stdout if omitted.")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"File Error: Input source file path '{args.input}' could not be located.")
        exit(1)

    with open(args.input, "r") as f:
        source_code_payload = f.read()

    initial_graph_state: MigrationState = {
        "file_path": args.input,
        "legacy_code": source_code_payload,
        "detected_anti_patterns": [],
        "retrieved_docs": [],
        "refactored_code": None,
        "validation_errors": None,
        "iteration_count": 0
    }

    print("Initializing Multi-Agent Code Migration Orchestrator...")
    app_graph = build_migration_graph()

    final_output_state = app_graph.invoke(initial_graph_state)

    print("\n================== PIPELINE RUN COMPLETE ==================")
    if final_output_state.get("validation_errors"):
        print("System halted with unresolved validation bugs.")
    else:
        refactored_code = final_output_state.get("refactored_code")
        if args.output:
            os.makedirs(os.path.dirname(args.output), exist_ok=True) if os.path.dirname(args.output) else None
            with open(args.output, "w") as f:
                f.write(refactored_code)
            print(f"Migrated code written to: {args.output}")
        else:
            print("Modernized Async Python Output:")
            print(refactored_code)
