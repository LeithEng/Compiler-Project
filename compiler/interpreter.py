"""
interpreter.py — lightweight execution engine for MiniLang AST.
Runs after successful semantic analysis and returns final top-level values.
"""

from .ast_nodes import (
    Program,
    VarDecl,
    Assignment,
    IfStmt,
    WhileStmt,
    BinOp,
    Identifier,
    IntLiteral,
    StringLiteral,
)
from .errors import ExecutionError


class _Cell:
    def __init__(self, name: str, var_type: str, value, line=None):
        self.name = name
        self.var_type = var_type
        self.value = value
        self.line = line


class _Env:
    def __init__(self, parent=None):
        self.parent = parent
        self._table: dict[str, _Cell] = {}

    def declare(self, name: str, var_type: str, line=None):
        if name in self._table:
            raise ExecutionError(f"Variable '{name}' already declared", line=line)
        default = 0 if var_type == "int" else ""
        self._table[name] = _Cell(name, var_type, default, line=line)

    def lookup_cell(self, name: str):
        if name in self._table:
            return self._table[name]
        if self.parent:
            return self.parent.lookup_cell(name)
        return None

    def assign(self, name: str, value, line=None):
        cell = self.lookup_cell(name)
        if cell is None:
            raise ExecutionError(f"Variable '{name}' not declared", line=line)
        cell.value = value

    def child(self):
        return _Env(parent=self)


class Interpreter:
    def __init__(self):
        self._root = _Env()
        self._steps = 0
        self._max_steps = 100000

    def run(self, tree: Program) -> list[dict]:
        self._exec_block(tree.statements, self._root)
        out = []
        for cell in self._root._table.values():
            out.append(
                {
                    "name": cell.name,
                    "type": cell.var_type,
                    "value": cell.value,
                    "line": cell.line,
                }
            )
        return out

    def _tick(self, line=None):
        self._steps += 1
        if self._steps > self._max_steps:
            raise ExecutionError("Execution step limit exceeded", line=line)

    def _exec_block(self, statements, env: _Env):
        for stmt in statements:
            self._tick(getattr(stmt, "line", None))
            self._exec_stmt(stmt, env)

    def _exec_stmt(self, node, env: _Env):
        if isinstance(node, VarDecl):
            env.declare(node.name, node.var_type, line=node.line)
            return

        if isinstance(node, Assignment):
            value = self._eval_expr(node.expr, env)
            env.assign(node.name, value, line=node.line)
            return

        if isinstance(node, IfStmt):
            cond = self._eval_expr(node.condition, env)
            if cond:
                self._exec_block(node.body, env.child())
            elif node.else_body:
                self._exec_block(node.else_body, env.child())
            return

        if isinstance(node, WhileStmt):
            while self._eval_expr(node.condition, env):
                self._tick(node.line)
                self._exec_block(node.body, env.child())
            return

        raise ExecutionError(f"Unknown statement node: {type(node).__name__}")

    def _eval_expr(self, node, env: _Env):
        if isinstance(node, IntLiteral):
            return node.value

        if isinstance(node, StringLiteral):
            return node.value

        if isinstance(node, Identifier):
            cell = env.lookup_cell(node.name)
            if cell is None:
                raise ExecutionError(
                    f"Variable '{node.name}' not declared", line=node.line
                )
            return cell.value

        if isinstance(node, BinOp):
            left = self._eval_expr(node.left, env)
            right = self._eval_expr(node.right, env)
            return self._apply_op(left, node.op, right, node.line)

        raise ExecutionError(f"Unknown expression node: {type(node).__name__}")

    def _apply_op(self, left, op: str, right, line=None):
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            if right == 0:
                raise ExecutionError("Division by zero", line=line)
            return int(left / right)
        if op == "==":
            return 1 if left == right else 0
        if op == "!=":
            return 1 if left != right else 0
        if op == ">":
            return 1 if left > right else 0
        if op == "<":
            return 1 if left < right else 0
        if op == ">=":
            return 1 if left >= right else 0
        if op == "<=":
            return 1 if left <= right else 0

        raise ExecutionError(f"Unsupported operator '{op}'", line=line)


def execute(tree: Program) -> list[dict]:
    return Interpreter().run(tree)
