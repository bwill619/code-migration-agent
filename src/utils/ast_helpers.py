import ast
from typing import Any, Dict

_SYNC_HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options"}
_FLASK_MODULES = {"flask", "flask_sqlalchemy", "flask_login", "flask_wtf"}
_FLASK_LIFECYCLE_HOOKS = {"before_request", "after_request", "teardown_request"}


class LegacyCodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.anti_patterns = []
        self.functions_found = []

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._scan_function(node)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def _scan_function(self, node: ast.AST):
        self.functions_found.append({
            "name": node.name,
            "lineno": node.lineno,
            "is_async": isinstance(node, ast.AsyncFunctionDef),
        })

        for decorator in node.decorator_list:
            self._check_flask_decorator(decorator)

        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                self._check_blocking_sleep(child)
                self._check_sync_http(child)
                self._check_flask_jsonify(child)

    def _check_blocking_sleep(self, node: ast.Call):
        if (isinstance(node.func, ast.Attribute) and
                node.func.attr == "sleep" and
                getattr(node.func.value, "id", None) == "time"):
            self.anti_patterns.append(
                f"Line {node.lineno}: Blocking 'time.sleep()' detected. Migrate to 'await asyncio.sleep()'."
            )

    def _check_sync_http(self, node: ast.Call):
        if (isinstance(node.func, ast.Attribute) and
                node.func.attr in _SYNC_HTTP_METHODS and
                getattr(node.func.value, "id", None) == "requests"):
            self.anti_patterns.append(
                f"Line {node.lineno}: Synchronous 'requests.{node.func.attr}()' detected. "
                f"Migrate to 'await httpx.AsyncClient().{node.func.attr}()'."
            )

    def _check_flask_jsonify(self, node: ast.Call):
        func = node.func
        is_jsonify = (
            (isinstance(func, ast.Name) and func.id == "jsonify") or
            (isinstance(func, ast.Attribute) and func.attr == "jsonify")
        )
        if is_jsonify:
            self.anti_patterns.append(
                f"Line {node.lineno}: 'jsonify()' detected. "
                "Migrate to a Pydantic response model or return a plain dict in FastAPI."
            )

    def _check_flask_decorator(self, decorator: ast.expr):
        attr = None
        lineno = getattr(decorator, "lineno", None)

        if isinstance(decorator, ast.Attribute):
            attr = decorator.attr
        elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
            attr = decorator.func.attr

        if attr in _FLASK_LIFECYCLE_HOOKS:
            self.anti_patterns.append(
                f"Line {lineno}: Flask '@app.{attr}' hook detected. "
                "Migrate to FastAPI middleware or lifespan events."
            )
        elif attr == "errorhandler":
            self.anti_patterns.append(
                f"Line {lineno}: Flask '@app.errorhandler' detected. "
                "Migrate to FastAPI exception handlers via '@app.exception_handler()'."
            )

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name in _FLASK_MODULES:
                self.anti_patterns.append(
                    f"Line {node.lineno}: Legacy '{alias.name}' import detected. Migrate to FastAPI equivalent."
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module and node.module.startswith("flask"):
            names = [alias.name for alias in node.names]
            if "Blueprint" in names:
                self.anti_patterns.append(
                    f"Line {node.lineno}: Flask 'Blueprint' import detected. Migrate to FastAPI 'APIRouter'."
                )
            else:
                self.anti_patterns.append(
                    f"Line {node.lineno}: Flask import 'from {node.module} import {', '.join(names)}' detected. "
                    "Migrate to FastAPI equivalents."
                )
        self.generic_visit(node)


def analyze_source_code(code_string: str) -> Dict[str, Any]:
    try:
        tree = ast.parse(code_string)
        analyzer = LegacyCodeAnalyzer()
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
            "error": f"AST Parsing Syntax error: {e.msg} at line {e.lineno}",
        }
