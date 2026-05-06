"""
compiler/__init__.py
Exposes a single compile_source() function that runs all three phases
and returns a structured result dict (consumed by the Flask API).
"""

from .lexer    import tokenize
from .parser   import Parser
from .semantic import SemanticAnalyzer
from .interpreter import execute
from .errors   import LexerError, ParseError, ExecutionError


def compile_source(source: str) -> dict:
    """
    Run all compiler phases on *source*.
    Always returns a dict; never raises — errors are collected inside.

    Return shape:
    {
        "success":      bool,
        "tokens":       [ {type, value, line}, … ],
        "ast":          str  | None,
        "symbols":      [ {name, type, line}, … ],
        "result":       [ {name, type, value, line}, … ],
        "errors":       [ {phase, line, message}, … ],
    }
    """
    result = {
        "success": False,
        "tokens": [],
        "ast": None,
        "symbols": [],
        "result": [],
        "errors": [],
    }

    # ── Phase 1: Lexing ────────────────────────────────────────────────────────
    try:
        tokens = tokenize(source)
        result["tokens"] = [t.to_dict() for t in tokens]
    except LexerError as e:
        result["errors"].append(e.to_dict())
        return result   # cannot continue without tokens

    # ── Phase 2: Parsing ───────────────────────────────────────────────────────
    try:
        parser = Parser(tokens)
        tree = parser.parse()
        result["ast"] = repr(tree)
    except ParseError as e:
        result["errors"].append(e.to_dict())
        return result   # cannot continue without an AST

    result["symbols"] = parser.symbol_table.to_list()
    if parser.semantic_errors:
        result["errors"] = [e.to_dict() for e in parser.semantic_errors]
        return result

    # ── Phase 3: Semantic analysis ─────────────────────────────────────────────
    analyzer = SemanticAnalyzer()
    sem_errors = analyzer.analyze(tree)
    if sem_errors:
        result["errors"] = [e.to_dict() for e in sem_errors]
        return result

    # ── Phase 4: Execution ────────────────────────────────────────────────────
    try:
        result["result"] = execute(tree)
    except ExecutionError as e:
        result["errors"].append(e.to_dict())
        return result

    result["success"] = True
    return result
