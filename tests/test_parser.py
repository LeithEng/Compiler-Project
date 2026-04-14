"""
tests/test_parser.py — Unit tests for the Parser (Milestone 2)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from compiler.lexer import tokenize
from compiler.parser import parse
from compiler.ast_nodes import *
from compiler.errors import ParseError


def ast(src):
    return parse(tokenize(src))


# ── Declarations ──────────────────────────────────────────────────────────────

def test_int_declaration():
    tree = ast("int x;")
    assert len(tree.statements) == 1
    node = tree.statements[0]
    assert isinstance(node, VarDecl)
    assert node.var_type == "int"
    assert node.name == "x"

def test_string_declaration():
    tree = ast('string name;')
    node = tree.statements[0]
    assert isinstance(node, VarDecl)
    assert node.var_type == "string"


# ── Assignments ───────────────────────────────────────────────────────────────

def test_simple_assignment():
    tree = ast("x = 5;")
    node = tree.statements[0]
    assert isinstance(node, Assignment)
    assert node.name == "x"
    assert isinstance(node.expr, IntLiteral)
    assert node.expr.value == 5

def test_addition_assignment():
    tree = ast("x = 3 + y;")
    node = tree.statements[0]
    assert isinstance(node.expr, BinOp)
    assert node.expr.op == "+"

def test_string_assignment():
    tree = ast('name = "Alice";')
    node = tree.statements[0]
    assert isinstance(node.expr, StringLiteral)
    assert node.expr.value == "Alice"

def test_parenthesized_expr():
    tree = ast("z = (x + 2) * 3;")
    assert isinstance(tree.statements[0].expr, BinOp)


# ── Control structures ────────────────────────────────────────────────────────

def test_if_no_else():
    tree = ast("if x > 0 then { y = 1; }")
    node = tree.statements[0]
    assert isinstance(node, IfStmt)
    assert node.else_body is None
    assert len(node.body) == 1

def test_if_else():
    tree = ast("if x > 0 then { y = 1; } else { y = 0; }")
    node = tree.statements[0]
    assert isinstance(node, IfStmt)
    assert node.else_body is not None

def test_while_loop():
    tree = ast("while x > 0 do { x = x - 1; }")
    node = tree.statements[0]
    assert isinstance(node, WhileStmt)
    assert len(node.body) == 1


# ── Multiple statements ────────────────────────────────────────────────────────

def test_multiple_stmts():
    src = "int x;\nint y;\nx = 5;\ny = x + 3;"
    tree = ast(src)
    assert len(tree.statements) == 4


# ── Error cases ───────────────────────────────────────────────────────────────

def test_missing_semicolon():
    with pytest.raises(ParseError):
        ast("x = 5")

def test_missing_then():
    with pytest.raises(ParseError):
        ast("if x > 0 { y = 1; }")

def test_empty_source():
    tree = ast("")
    assert tree.statements == []
