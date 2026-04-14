"""
parser.py — Milestone 2: Syntax Analysis
Recursive-descent parser.  Produces an AST from the token list.

Grammar (extended from the project spec):
─────────────────────────────────────────
program     ::= stmt*
stmt        ::= var_decl
              | assignment
              | if_stmt
              | while_stmt
var_decl    ::= ('int'|'string') ID ';'
assignment  ::= ID '=' expr ';'
if_stmt     ::= 'if' expr 'then' '{' stmt* '}' ('else' '{' stmt* '}')?
while_stmt  ::= 'while' expr 'do' '{' stmt* '}'
expr        ::= comparison
comparison  ::= addition (('=='|'!='|'>'|'<'|'>='|'<=') addition)?
addition    ::= term (('+' | '-') term)*
term        ::= factor (('*' | '/') factor)*
factor      ::= NUM | STR | ID | '(' expr ')'
"""

from .ast_nodes import (
    Program, VarDecl, Assignment, IfStmt, WhileStmt,
    BinOp, Identifier, IntLiteral, StringLiteral,
)
from .errors import ParseError
from .lexer import Token

COMPARISON_OPS = {"==", "!=", ">", "<", ">=", "<="}


class Parser:
    def __init__(self, tokens: list[Token]):
        self._tokens = tokens
        self._pos = 0

    # ── Low-level helpers ──────────────────────────────────────────────────────

    def _peek(self) -> Token | None:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _advance(self) -> Token:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _check(self, type_: str, value=None) -> bool:
        tok = self._peek()
        if tok is None:
            return False
        if tok.type != type_:
            return False
        if value is not None and tok.value != value:
            return False
        return True

    def _expect(self, type_: str, value=None) -> Token:
        tok = self._peek()
        if tok is None:
            raise ParseError(
                f"Unexpected end of input; expected {value or type_}"
            )
        if tok.type != type_ or (value is not None and tok.value != value):
            raise ParseError(
                f"Expected {value or type_!r}, got {tok.value!r}",
                line=tok.line,
            )
        return self._advance()

    def _current_line(self) -> int | None:
        tok = self._peek()
        return tok.line if tok else None

    # ── Top-level ──────────────────────────────────────────────────────────────

    def parse(self) -> Program:
        stmts = []
        while self._peek() is not None:
            stmts.append(self._parse_stmt())
        return Program(stmts)

    # ── Statements ──────────────────────────────────────────────────────────────

    def _parse_stmt(self):
        tok = self._peek()
        if tok is None:
            raise ParseError("Unexpected end of input")

        # Variable declaration: int x; or string name;
        if tok.type == "KW" and tok.value in ("int", "string"):
            return self._parse_var_decl()

        # if statement
        if tok.type == "KW" and tok.value == "if":
            return self._parse_if()

        # while statement
        if tok.type == "KW" and tok.value == "while":
            return self._parse_while()

        # assignment: ID = expr;
        if tok.type == "ID":
            return self._parse_assignment()

        raise ParseError(
            f"Unexpected token {tok.value!r} at start of statement",
            line=tok.line,
        )

    def _parse_var_decl(self) -> VarDecl:
        type_tok = self._advance()           # 'int' or 'string'
        name_tok = self._expect("ID")
        self._expect("PUNCT", ";")
        return VarDecl(type_tok.value, name_tok.value, line=type_tok.line)

    def _parse_assignment(self) -> Assignment:
        name_tok = self._advance()           # ID
        self._expect("OP", "=")
        expr = self._parse_expr()
        self._expect("PUNCT", ";")
        return Assignment(name_tok.value, expr, line=name_tok.line)

    def _parse_if(self) -> IfStmt:
        line = self._peek().line
        self._advance()                      # 'if'
        condition = self._parse_expr()
        self._expect("KW", "then")
        self._expect("PUNCT", "{")
        body = self._parse_block()
        self._expect("PUNCT", "}")

        else_body = None
        if self._check("KW", "else"):
            self._advance()                  # 'else'
            self._expect("PUNCT", "{")
            else_body = self._parse_block()
            self._expect("PUNCT", "}")

        return IfStmt(condition, body, else_body, line=line)

    def _parse_while(self) -> WhileStmt:
        line = self._peek().line
        self._advance()                      # 'while'
        condition = self._parse_expr()
        self._expect("KW", "do")
        self._expect("PUNCT", "{")
        body = self._parse_block()
        self._expect("PUNCT", "}")
        return WhileStmt(condition, body, line=line)

    def _parse_block(self) -> list:
        stmts = []
        while not self._check("PUNCT", "}") and self._peek() is not None:
            stmts.append(self._parse_stmt())
        return stmts

    # ── Expressions (recursive descent) ────────────────────────────────────────

    def _parse_expr(self):
        return self._parse_comparison()

    def _parse_comparison(self):
        left = self._parse_addition()
        tok = self._peek()
        if tok and tok.type == "OP" and tok.value in COMPARISON_OPS:
            op = self._advance().value
            right = self._parse_addition()
            return BinOp(left, op, right, line=tok.line)
        return left

    def _parse_addition(self):
        left = self._parse_term()
        while True:
            tok = self._peek()
            if tok and tok.type == "OP" and tok.value in ("+", "-"):
                op = self._advance().value
                right = self._parse_term()
                left = BinOp(left, op, right, line=tok.line)
            else:
                break
        return left

    def _parse_term(self):
        left = self._parse_factor()
        while True:
            tok = self._peek()
            if tok and tok.type == "OP" and tok.value in ("*", "/"):
                op = self._advance().value
                right = self._parse_factor()
                left = BinOp(left, op, right, line=tok.line)
            else:
                break
        return left

    def _parse_factor(self):
        tok = self._peek()
        if tok is None:
            raise ParseError("Unexpected end of input in expression")

        if tok.type == "NUM":
            self._advance()
            return IntLiteral(tok.value, line=tok.line)

        if tok.type == "STR":
            self._advance()
            return StringLiteral(tok.value, line=tok.line)

        if tok.type == "ID":
            self._advance()
            return Identifier(tok.value, line=tok.line)

        if tok.type == "PUNCT" and tok.value == "(":
            self._advance()          # '('
            expr = self._parse_expr()
            self._expect("PUNCT", ")")
            return expr

        raise ParseError(
            f"Unexpected token {tok.value!r} in expression", line=tok.line
        )


# ── Convenience wrapper ────────────────────────────────────────────────────────

def parse(tokens) -> Program:
    return Parser(tokens).parse()
