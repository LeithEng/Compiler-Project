"""
semantic.py — Milestone 3: Semantic Analysis
Walks the AST, builds a symbol table, checks types and scopes.
Returns a list of SemanticError objects (does not raise immediately
so all errors in a file are collected in one pass).
"""

from .ast_nodes import (
    Program, VarDecl, Assignment, IfStmt, WhileStmt,
    BinOp, Identifier, IntLiteral, StringLiteral,
)
from .errors import SemanticError
from .symbol_table import SymbolTable

# Operators that are only valid between integers
INT_ONLY_OPS = {"-", "*", "/", ">", "<", ">=", "<="}
# Operators valid for both types (strings can be compared with == / !=, concatenated with +)
COMPARISON_OPS = {"==", "!=", ">", "<", ">=", "<="}


class SemanticAnalyzer:
    def __init__(self):
        self.errors: list[SemanticError] = []
        self.symbol_table = SymbolTable()

    # ── Public entry point ─────────────────────────────────────────────────────

    def analyze(self, tree: Program) -> list[SemanticError]:
        self._visit_program(tree)
        return self.errors

    # ── Visitors ───────────────────────────────────────────────────────────────

    def _visit_program(self, node: Program):
        for stmt in node.statements:
            self._visit_stmt(stmt, self.symbol_table)

    def _visit_stmt(self, node, scope: SymbolTable):
        if isinstance(node, VarDecl):
            self._visit_var_decl(node, scope)
        elif isinstance(node, Assignment):
            self._visit_assignment(node, scope)
        elif isinstance(node, IfStmt):
            self._visit_if(node, scope)
        elif isinstance(node, WhileStmt):
            self._visit_while(node, scope)
        else:
            self._error(f"Unknown statement type: {type(node).__name__}")

    def _visit_var_decl(self, node: VarDecl, scope: SymbolTable):
        ok = scope.declare(node.name, node.var_type, node.line)
        if not ok:
            self._error(
                f"Variable '{node.name}' already declared in this scope",
                node.line,
            )

    def _visit_assignment(self, node: Assignment, scope: SymbolTable):
        sym = scope.lookup(node.name)
        if sym is None:
            self._error(
                f"Variable '{node.name}' used before declaration", node.line
            )
            # Still evaluate the expression to catch further errors
            self._infer_type(node.expr, scope)
            return

        expr_type = self._infer_type(node.expr, scope)
        if expr_type and expr_type != sym.var_type:
            self._error(
                f"Type mismatch: cannot assign {expr_type} to '{node.name}' "
                f"(declared as {sym.var_type})",
                node.line,
            )

    def _visit_if(self, node: IfStmt, scope: SymbolTable):
        self._infer_type(node.condition, scope)
        inner = scope.enter_scope()
        for stmt in node.body:
            self._visit_stmt(stmt, inner)
        if node.else_body:
            else_scope = scope.enter_scope()
            for stmt in node.else_body:
                self._visit_stmt(stmt, else_scope)

    def _visit_while(self, node: WhileStmt, scope: SymbolTable):
        self._infer_type(node.condition, scope)
        inner = scope.enter_scope()
        for stmt in node.body:
            self._visit_stmt(stmt, inner)

    # ── Type inference ─────────────────────────────────────────────────────────

    def _infer_type(self, node, scope: SymbolTable) -> str | None:
        """Return the inferred type ('int'|'string') or None on error."""

        if isinstance(node, IntLiteral):
            return "int"

        if isinstance(node, StringLiteral):
            return "string"

        if isinstance(node, Identifier):
            sym = scope.lookup(node.name)
            if sym is None:
                self._error(
                    f"Undeclared variable '{node.name}'", node.line
                )
                return None
            return sym.var_type

        if isinstance(node, BinOp):
            return self._check_binop(node, scope)

        self._error(f"Unknown expression node: {type(node).__name__}")
        return None

    def _check_binop(self, node: BinOp, scope: SymbolTable) -> str | None:
        left_type  = self._infer_type(node.left,  scope)
        right_type = self._infer_type(node.right, scope)

        # If either side failed inference already, don't pile on
        if left_type is None or right_type is None:
            return None

        if left_type != right_type:
            self._error(
                f"Type mismatch in '{node.op}': "
                f"left is {left_type}, right is {right_type}",
                node.line,
            )
            return None

        # Strings only support '+' (concatenation) and '==' / '!='
        if left_type == "string" and node.op in INT_ONLY_OPS:
            self._error(
                f"Operator '{node.op}' is not valid for string operands",
                node.line,
            )
            return None

        # Comparison operators always return a logical int (0/1)
        if node.op in COMPARISON_OPS:
            return "int"

        return left_type


    # ── Helper ─────────────────────────────────────────────────────────────────

    def _error(self, message: str, line=None):
        self.errors.append(SemanticError(message, line=line))


# ── Convenience wrapper ────────────────────────────────────────────────────────

def analyze(tree) -> list[SemanticError]:
    return SemanticAnalyzer().analyze(tree)
