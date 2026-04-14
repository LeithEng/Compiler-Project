"""
errors.py — Unified error types for all compiler phases.
"""


class CompilerError(Exception):
    """Base class for all compiler errors."""
    def __init__(self, message, line=None):
        self.message = message
        self.line = line
        super().__init__(self._format())

    def _format(self):
        prefix = f"[Line {self.line}] " if self.line is not None else ""
        return f"{prefix}{self.__class__.__name__}: {self.message}"

    def to_dict(self):
        return {
            "phase": self.__class__.__name__,
            "line": self.line,
            "message": self.message,
        }


class LexerError(CompilerError):
    """Raised when the lexer encounters an unexpected character."""
    pass


class ParseError(CompilerError):
    """Raised when the parser finds a syntax violation."""
    pass


class SemanticError(CompilerError):
    """Raised when the semantic analyzer finds a type or scope error."""
    pass


class ExecutionError(CompilerError):
    """Raised when runtime execution fails (e.g., division by zero)."""
    pass
