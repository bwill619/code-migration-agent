from typing import List, TypedDict, Optional

class MigrationState(TypedDict):
    """
    State object managing the codebase refactoring loop.
    """
    file_path: str                 # Original legacy file path
    legacy_code: str               # Raw content of the source code
    detected_anti_patterns: List[str] # Specific lines/functions needing updates
    retrieved_docs: List[str]      # Matching documentation snippets from Qdrant
    refactored_code: Optional[str] # Current iteration of the upgraded code
    validation_errors: Optional[str] # Standard error / test stack traces if validation fails
    iteration_count: int           # Halts infinite loops if a fix keeps failing
