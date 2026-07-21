import os
import glob
import json
import argparse
from datetime import datetime, timezone
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()

from src.agents.state import MigrationState
from src.agents.parser import parser_node
from src.agents.retriever import retriever_node
from src.agents.refactorer import refactorer_node
from src.agents.validator import validator_node


def route_validation_results(state: MigrationState):
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
    workflow.add_node("parser_agent", parser_node)
    workflow.add_node("retriever_agent", retriever_node)
    workflow.add_node("refactorer_agent", refactorer_node)
    workflow.add_node("validator_agent", validator_node)
    workflow.set_entry_point("parser_agent")
    workflow.add_edge("parser_agent", "retriever_agent")
    workflow.add_edge("retriever_agent", "refactorer_agent")
    workflow.add_edge("refactorer_agent", "validator_agent")
    workflow.add_conditional_edges(
        "validator_agent",
        route_validation_results,
        {"retriever_agent": "retriever_agent", END: END}
    )
    return workflow.compile()


def discover_files(input_path: str) -> list[str]:
    """Returns all .py files to process — a single file or every .py in a directory tree."""
    if os.path.isfile(input_path):
        return [input_path]
    return sorted(glob.glob(os.path.join(input_path, "**", "*.py"), recursive=True))


def resolve_output_path(input_file: str, input_root: str, output_root: str | None) -> str | None:
    """Maps an input file path to its corresponding output path."""
    if output_root is None:
        return None
    if os.path.isfile(input_root):
        return output_root
    rel = os.path.relpath(input_file, input_root)
    return os.path.join(output_root, rel)


def run_file(graph, input_file: str, output_path: str | None) -> dict:
    """Runs the migration pipeline on a single file and returns a result record."""
    with open(input_file) as f:
        source = f.read()

    state: MigrationState = {
        "file_path": input_file,
        "legacy_code": source,
        "detected_anti_patterns": [],
        "retrieved_docs": [],
        "refactored_code": None,
        "validation_errors": None,
        "iteration_count": 0,
    }

    final = graph.invoke(state)
    success = not final.get("validation_errors")

    if success and output_path:
        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        with open(output_path, "w") as f:
            f.write(final["refactored_code"])

    return {
        "input": input_file,
        "output": output_path,
        "patterns_detected": len(final.get("detected_anti_patterns", [])),
        "docs_retrieved": len(final.get("retrieved_docs", [])),
        "iterations": final.get("iteration_count", 0),
        "status": "success" if success else "failed",
        "refactored_code": final.get("refactored_code"),
    }


def write_report(results: list[dict], report_path: str):
    """Writes a JSON evaluation report summarising all processed files."""
    succeeded = sum(1 for r in results if r["status"] == "success")
    total = len(results)
    avg_iter = sum(r["iterations"] for r in results) / total if total else 0

    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_files": total,
            "succeeded": succeeded,
            "failed": total - succeeded,
            "pass_rate": f"{succeeded / total * 100:.1f}%" if total else "N/A",
            "avg_iterations": round(avg_iter, 2),
        },
        "files": [
            {k: v for k, v in r.items() if k != "refactored_code"}
            for r in results
        ],
    }

    out_dir = os.path.dirname(report_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report written to: {report_path}")


def print_summary(results: list[dict]):
    succeeded = sum(1 for r in results if r["status"] == "success")
    total = len(results)
    print(f"\n{'=' * 58}")
    print(f"PIPELINE RUN COMPLETE — {succeeded}/{total} files migrated successfully")
    print(f"{'=' * 58}")
    for r in results:
        tag = "OK    " if r["status"] == "success" else "FAILED"
        dest = f"-> {r['output']}" if r["output"] else "(stdout)"
        print(f"  [{tag}]  {r['input']}  {dest}")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(
        description="Run Autonomous Code Migration Multi-Agent RAG Pipeline."
    )
    arg_parser.add_argument(
        "--input", required=True,
        help="Path to a legacy Python file or a directory of files to migrate."
    )
    arg_parser.add_argument(
        "--output", required=False,
        help="Output file (single-file mode) or directory (directory mode). Prints to stdout if omitted."
    )
    arg_parser.add_argument(
        "--report", required=False,
        help="Path to write a JSON evaluation report after the run."
    )
    args = arg_parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: '{args.input}' not found.")
        exit(1)

    files = discover_files(args.input)
    if not files:
        print(f"No Python files found in '{args.input}'.")
        exit(1)

    print("Initializing Multi-Agent Code Migration Orchestrator...")
    print(f"Files to process: {len(files)}")
    graph = build_migration_graph()

    results = []
    for f in files:
        print(f"\n{'=' * 58}")
        print(f"Processing: {f}")
        out = resolve_output_path(f, args.input, args.output)
        result = run_file(graph, f, out)
        results.append(result)

    print_summary(results)

    if args.report:
        write_report(results, args.report)

    # Single file with no --output: print migrated code to stdout
    if len(results) == 1 and results[0]["status"] == "success" and not args.output:
        print("\nModernized Async Python Output:")
        print(results[0]["refactored_code"])
    elif len(results) > 1 and not args.output:
        print("\nNote: use --output <dir> to save migrated files to disk.")
