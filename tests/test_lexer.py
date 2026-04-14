"""
tests/test_lexer.py — Unit tests for the Lexer (Milestone 1)
Run with:  python -m pytest tests/
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from compiler.lexer import tokenize, Token
from compiler.errors import LexerError


def types(src): return [t.type for t in tokenize(src)]
def vals(src):  return [t.value for t in tokenize(src)]


# ── Basic token types ──────────────────────────────────────────────────────────

def test_integer_literal():
    assert vals("42") == [42]
    assert types("42") == ["NUM"]

def test_identifier():
    assert types("myVar") == ["ID"]
    assert vals("myVar") == ["myVar"]

def test_keywords():
    src = "if then else while do int string"
    assert types(src) == ["KW"] * 7

def test_operators():
    src = "= + - * / > < == != >= <="
    assert types(src) == ["OP"] * 11

def test_string_literal():
    toks = tokenize('"hello world"')
    assert toks[0].type == "STR"
    assert toks[0].value == "hello world"   # quotes stripped

def test_punctuation():
    assert types("( ) { } ; ,") == ["PUNCT"] * 6


# ── Combined expressions ───────────────────────────────────────────────────────

def test_assignment_expr():
    toks = tokenize("x = 5 + 2;")
    assert [(t.type, t.value) for t in toks] == [
        ("ID", "x"), ("OP", "="), ("NUM", 5),
        ("OP", "+"), ("NUM", 2), ("PUNCT", ";"),
    ]

def test_complex_expr():
    toks = tokenize("z = x * (y - 3);")
    types_ = [t.type for t in toks]
    assert "PUNCT" in types_
    assert "OP" in types_

def test_if_else():
    src = "if a == b then a = a + 1; else b = b - 1;"
    t = tokenize(src)
    kws = [tok.value for tok in t if tok.type == "KW"]
    assert kws == ["if", "then", "else"]


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_source():
    assert tokenize("") == []

def test_whitespace_only():
    assert tokenize("   \t  \n  ") == []

def test_comment_ignored():
    toks = tokenize("x = 5; // this is a comment\ny = 3;")
    assert all(t.type != "COMMENT" for t in toks)
    assert len(toks) == 8   # x = 5 ; y = 3 ;

def test_multiline_line_tracking():
    src = "int x;\nint y;\n"
    toks = tokenize(src)
    # toks: [KW(int)@1, ID(x)@1, PUNCT(;)@1, KW(int)@2, ID(y)@2, PUNCT(;)@2]
    assert toks[0].line == 1   # 'int' on line 1
    assert toks[3].line == 2   # 'int' on line 2

def test_string_with_spaces():
    toks = tokenize('"hello world"')
    assert toks[0].value == "hello world"

def test_unknown_character_raises():
    with pytest.raises(LexerError):
        tokenize("x = 5 @ 2;")
