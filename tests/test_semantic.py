"""
tests/test_semantic.py — Unit tests for the Semantic Analyzer (Milestone 3)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from compiler.lexer import tokenize
from compiler.parser import parse
from compiler.semantic import analyze


def errors(src):
    tree = parse(tokenize(src))
    return analyze(tree)

def ok(src):
    return len(errors(src)) == 0

def has_error(src, keyword):
    errs = errors(src)
    return any(keyword.lower() in e.message.lower() for e in errs)


# ── Valid programs ─────────────────────────────────────────────────────────────

def test_valid_int_program():
    src = "int x;\nx = 5;\nint y;\ny = x + 3;"
    assert ok(src)

def test_valid_string_program():
    src = 'string name;\nname = "Alice";'
    assert ok(src)

def test_valid_if():
    src = "int x;\nx = 10;\nif x > 5 then { x = x - 1; }"
    assert ok(src)

def test_valid_while():
    src = "int x;\nx = 3;\nwhile x > 0 do { x = x - 1; }"
    assert ok(src)

def test_string_concatenation():
    src = 'string a;\nstring b;\na = "hello";\nb = a + " world";'
    assert ok(src)


# ── Type errors ───────────────────────────────────────────────────────────────

def test_assign_string_to_int():
    src = 'int x;\nx = "hello";'
    assert has_error(src, "mismatch")

def test_assign_int_to_string():
    src = "string s;\ns = 42;"
    assert has_error(src, "mismatch")

def test_add_int_and_string():
    src = 'int x;\nstring s;\nx = 1;\ns = "hi";\nx = x + s;'
    assert has_error(src, "mismatch")

def test_subtract_strings():
    src = 'string a;\nstring b;\na = "x";\nb = "y";\na = a - b;'
    assert has_error(src, "not valid for string")


# ── Scope errors ──────────────────────────────────────────────────────────────

def test_undeclared_variable():
    assert has_error("x = 5;", "declaration")

def test_use_before_declare():
    assert has_error("y = x + 1;", "undeclared")

def test_double_declaration():
    src = "int x;\nint x;"
    assert has_error(src, "already declared")


# ── Symbol table ──────────────────────────────────────────────────────────────

def test_symbol_table_populated():
    from compiler.semantic import SemanticAnalyzer
    from compiler.parser import parse
    from compiler.lexer import tokenize
    src = "int x;\nstring name;"
    tree = parse(tokenize(src))
    sa = SemanticAnalyzer()
    sa.analyze(tree)
    syms = {s.name: s.var_type for s in sa.symbol_table.all_symbols()}
    assert syms == {"x": "int", "name": "string"}
