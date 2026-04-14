"""
lexer.py — Milestone 1: Lexical Analysis
Converts raw source code into a flat list of Token objects.
"""

import re
from .errors import LexerError


# ── Token definition ──────────────────────────────────────────────────────────

class Token:
    __slots__ = ("type", "value", "line")

    def __init__(self, type_: str, value, line: int):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        if self.type in ("ID", "NUM", "STR", "KW"):
            return f"{self.type}({self.value!r})"
        return repr(self.value)

    def to_dict(self):
        return {"type": self.type, "value": self.value, "line": self.line}


# ── Token specification ───────────────────────────────────────────────────────

KEYWORDS = {"if", "then", "else", "while", "do", "int", "string"}

# Order matters: longer / more specific patterns first.
TOKEN_SPEC = [
    ("COMMENT", r'//[^\n]*'),          # single-line comment (ignored) — must be before OP
    ("STR",     r'"[^"]*"'),           # string literal  "hello"
    ("NUM",     r'\d+'),               # integer literal
    ("ID",      r'[A-Za-z_]\w*'),      # identifier / keyword
    ("OP",      r'==|!=|>=|<=|[+\-*/=<>]'),  # operators
    ("PUNCT",   r'[(){};,]'),          # punctuation
    ("NEWLINE", r'\n'),                # track line numbers
    ("SKIP",    r'[ \t]+'),            # whitespace (ignored)
    ("MISMATCH",r'.'),                 # anything else → error
]

MASTER_PATTERN = re.compile(
    "|".join(f"(?P<{name}>{pat})" for name, pat in TOKEN_SPEC)
)


# ── Lexer ─────────────────────────────────────────────────────────────────────

class Lexer:
    def __init__(self, source: str):
        self.source = source

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        line = 1

        for mo in MASTER_PATTERN.finditer(self.source):
            kind = mo.lastgroup
            value = mo.group()

            if kind == "NEWLINE":
                line += 1
            elif kind in ("SKIP", "COMMENT"):
                pass   # discard whitespace and comments
            elif kind == "MISMATCH":
                raise LexerError(
                    f"Unexpected character {value!r}", line=line
                )
            else:
                # Distinguish keywords from identifiers
                if kind == "ID" and value in KEYWORDS:
                    kind = "KW"
                # Strip quotes from string literals
                if kind == "STR":
                    value = value[1:-1]
                # Convert number literals to int
                if kind == "NUM":
                    value = int(value)

                tokens.append(Token(kind, value, line))

        return tokens


def tokenize(source: str) -> list[Token]:
    """Convenience wrapper."""
    return Lexer(source).tokenize()
