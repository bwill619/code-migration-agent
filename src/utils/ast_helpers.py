import ast
from typing import Any, Dict


class LegacacyCodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.anti_patterns = []
        self.functions_found = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._scan_function(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._scan_function(node)
        self.generic_visit(node)

    def _scan_function(self, node: ast.AST):
        """Scans individual functions for legacy patterns"""
        func_info = {
            "name": node.name,
            "lineno": node.lineno,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
        }
        self.functions_found.append(func_info)

        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                if child.func.attr == "sleep" and getattr(child.func.value, "id", None) == "time":
                    self.anti_patterns.append(
                        f"Line {child.lineno}: Found blocking 'time.sleep()'. Needs migration to 'await asyncio.sleep()'."
                    )

    def visit_Import(self, node: ast.Import):
        """Flags legacy framework imports"""
        for alias in node.names:
            if alias.name == "flask":
                self.anti_patterns.append(
                    f"Line {node.lineno}: Legacy Flask import detected. Consider migrating to FastAPI."
                )
        self.generic_visit(node)


def analyze_source_code(code_string: str) -> Dict[str, Any]:
    """Parses code text into an AST and extracts architectural features"""
    try:
        tree = ast.parse(code_string)
        analyzer = LegacacyCodeAnalyzer()
        analyzer.visit(tree)
        return {
            "anti_patterns": analyzer.anti_patterns,
            "functions": analyzer.functions_found,
            "error": None,
        }
    except SyntaxError as e:
        return {
            "anti_patterns": [],
            "functions": [],
            "error": f"AST Parsing Syntax error at line {e.msg} at line {e.lineno}",
        }
