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
from .errors import ParseError, SemanticError
from .lexer import Token
from .symbol_table import SymbolTable

COMPARISON_OPS = {"==", "!=", ">", "<", ">=", "<="}
INT_ONLY_OPS = {"-", "*", "/", ">", "<", ">=", "<="}


class Parser:
    def __init__(self, tokens: list[Token]):
        self._tokens = tokens
        self._pos = 0
        self._semantic_errors: list[SemanticError] = []
        self._symbols = SymbolTable()

    @property
    def semantic_errors(self) -> list[SemanticError]:
        return self._semantic_errors

    @property
    def symbol_table(self) -> SymbolTable:
        return self._symbols

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
            stmts.append(self._parse_stmt(self._symbols))
        return Program(stmts)

    # ── Statements ──────────────────────────────────────────────────────────────

    def _parse_stmt(self, scope: SymbolTable):
        tok = self._peek()
        if tok is None:
            raise ParseError("Unexpected end of input")

        # Variable declaration: int x; or string name;
        if tok.type == "KW" and tok.value in ("int", "string"):
            return self._parse_var_decl(scope)

        # if statement
        if tok.type == "KW" and tok.value == "if":
            return self._parse_if(scope)

        # while statement
        if tok.type == "KW" and tok.value == "while":
            return self._parse_while(scope)

        # assignment: ID = expr;
        if tok.type == "ID":
            return self._parse_assignment(scope)

        raise ParseError(
            f"Unexpected token {tok.value!r} at start of statement",
            line=tok.line,
        )

    def _parse_var_decl(self, scope: SymbolTable) -> VarDecl:
        type_tok = self._advance()           # 'int' or 'string'
        name_tok = self._expect("ID")
        self._expect("PUNCT", ";")
        ok = scope.declare(name_tok.value, type_tok.value, name_tok.line)
        if not ok:
            self._semantic_errors.append(
                SemanticError(
                    f"Variable '{name_tok.value}' already declared in this scope",
                    line=name_tok.line,
                )
            )
        return VarDecl(type_tok.value, name_tok.value, line=type_tok.line)

    def _parse_assignment(self, scope: SymbolTable) -> Assignment:
        name_tok = self._advance()           # ID
        self._expect("OP", "=")
        expr, expr_type = self._parse_expr(scope)
        self._expect("PUNCT", ";")
        sym = scope.lookup(name_tok.value)
        if sym is None:
            self._semantic_errors.append(
                SemanticError(
                    f"Variable '{name_tok.value}' used before declaration",
                    line=name_tok.line,
                )
            )
        elif expr_type and expr_type != sym.var_type:
            self._semantic_errors.append(
                SemanticError(
                    f"Type mismatch: cannot assign {expr_type} to '{name_tok.value}' "
                    f"(declared as {sym.var_type})",
                    line=name_tok.line,
                )
            )
        return Assignment(name_tok.value, expr, line=name_tok.line)

    def _parse_if(self, scope: SymbolTable) -> IfStmt:
        line = self._peek().line
        self._advance()                      # 'if'
        condition, _ = self._parse_expr(scope)
        self._expect("KW", "then")
        self._expect("PUNCT", "{")
        body = self._parse_block(scope.enter_scope())
        self._expect("PUNCT", "}")

        else_body = None
        if self._check("KW", "else"):
            self._advance()                  # 'else'
            self._expect("PUNCT", "{")
            else_body = self._parse_block(scope.enter_scope())
            self._expect("PUNCT", "}")

        return IfStmt(condition, body, else_body, line=line)

    def _parse_while(self, scope: SymbolTable) -> WhileStmt:
        line = self._peek().line
        self._advance()                      # 'while'
        condition, _ = self._parse_expr(scope)
        self._expect("KW", "do")
        self._expect("PUNCT", "{")
        body = self._parse_block(scope.enter_scope())
        self._expect("PUNCT", "}")
        return WhileStmt(condition, body, line=line)

    def _parse_block(self, scope: SymbolTable) -> list:
        stmts = []
        while not self._check("PUNCT", "}") and self._peek() is not None:
            stmts.append(self._parse_stmt(scope))
        return stmts

    # ── Expressions (recursive descent) ────────────────────────────────────────

    def _parse_expr(self, scope: SymbolTable):
        return self._parse_comparison(scope)

    def _parse_comparison(self, scope: SymbolTable):
        left, left_type = self._parse_addition(scope)
        tok = self._peek()
        if tok and tok.type == "OP" and tok.value in COMPARISON_OPS:
            op = self._advance().value
            right, right_type = self._parse_addition(scope)
            expr_type = self._combine_types(left_type, right_type, op, tok.line)
            return BinOp(left, op, right, line=tok.line), expr_type
        return left, left_type

    def _parse_addition(self, scope: SymbolTable):
        left, left_type = self._parse_term(scope)
        while True:
            tok = self._peek()
            if tok and tok.type == "OP" and tok.value in ("+", "-"):
                op = self._advance().value
                right, right_type = self._parse_term(scope)
                left_type = self._combine_types(left_type, right_type, op, tok.line)
                left = BinOp(left, op, right, line=tok.line)
            else:
                break
        return left, left_type

    def _parse_term(self, scope: SymbolTable):
        left, left_type = self._parse_factor(scope)
        while True:
            tok = self._peek()
            if tok and tok.type == "OP" and tok.value in ("*", "/"):
                op = self._advance().value
                right, right_type = self._parse_factor(scope)
                left_type = self._combine_types(left_type, right_type, op, tok.line)
                left = BinOp(left, op, right, line=tok.line)
            else:
                break
        return left, left_type

    def _parse_factor(self, scope: SymbolTable):
        tok = self._peek()
        if tok is None:
            raise ParseError("Unexpected end of input in expression")

        if tok.type == "NUM":
            self._advance()
            return IntLiteral(tok.value, line=tok.line), "int"

        if tok.type == "STR":
            self._advance()
            return StringLiteral(tok.value, line=tok.line), "string"

        if tok.type == "ID":
            self._advance()
            sym = scope.lookup(tok.value)
            if sym is None:
                self._semantic_errors.append(
                    SemanticError(
                        f"Undeclared variable '{tok.value}'",
                        line=tok.line,
                    )
                )
                return Identifier(tok.value, line=tok.line), None
            return Identifier(tok.value, line=tok.line), sym.var_type

        if tok.type == "PUNCT" and tok.value == "(":
            self._advance()          # '('
            expr, expr_type = self._parse_expr(scope)
            self._expect("PUNCT", ")")
            return expr, expr_type

        raise ParseError(
            f"Unexpected token {tok.value!r} in expression", line=tok.line
        )

    def _combine_types(self, left_type, right_type, op: str, line=None):
        if left_type is None or right_type is None:
            return None

        if left_type != right_type:
            self._semantic_errors.append(
                SemanticError(
                    f"Type mismatch in '{op}': left is {left_type}, right is {right_type}",
                    line=line,
                )
            )
            return None

        if left_type == "string" and op in INT_ONLY_OPS:
            self._semantic_errors.append(
                SemanticError(
                    f"Operator '{op}' is not valid for string operands",
                    line=line,
                )
            )
            return None

        if op in COMPARISON_OPS:
            return "int"

        return left_type


# ── Convenience wrapper ────────────────────────────────────────────────────────

def parse(tokens) -> Program:
    return Parser(tokens).parse()
