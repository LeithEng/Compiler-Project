"""
ast_nodes.py — AST node definitions for the compiler.
Every node stores its line number so errors can point back to source.
"""


class ASTNode:
    """Base class for all AST nodes."""
    pass


# ── Statements ────────────────────────────────────────────────────────────────

class Program(ASTNode):
    """Root node; holds a list of statements."""
    def __init__(self, statements):
        self.statements = statements  # list[ASTNode]

    def __repr__(self):
        return f"Program({self.statements})"


class VarDecl(ASTNode):
    """int x;  or  string name;"""
    def __init__(self, var_type, name, line=None):
        self.var_type = var_type  # 'int' | 'string'
        self.name = name          # str
        self.line = line

    def __repr__(self):
        return f"VarDecl({self.var_type}, {self.name})"


class Assignment(ASTNode):
    """x = <expr>;"""
    def __init__(self, name, expr, line=None):
        self.name = name   # str
        self.expr = expr   # ASTNode
        self.line = line

    def __repr__(self):
        return f"Assign({self.name}, {self.expr})"


class IfStmt(ASTNode):
    """if <cond> then { <body> } [else { <else_body> }]"""
    def __init__(self, condition, body, else_body=None, line=None):
        self.condition = condition    # ASTNode
        self.body = body              # list[ASTNode]
        self.else_body = else_body    # list[ASTNode] | None
        self.line = line

    def __repr__(self):
        return f"If({self.condition}, body={self.body}, else={self.else_body})"


class WhileStmt(ASTNode):
    """while <cond> do { <body> }"""
    def __init__(self, condition, body, line=None):
        self.condition = condition
        self.body = body
        self.line = line

    def __repr__(self):
        return f"While({self.condition}, {self.body})"


# ── Expressions ───────────────────────────────────────────────────────────────

class BinOp(ASTNode):
    """left OP right  (e.g. x + 2, a > b)"""
    def __init__(self, left, op, right, line=None):
        self.left = left
        self.op = op      # str: '+' '-' '*' '/' '>' '<' '==' '!=' '>=' '<='
        self.right = right
        self.line = line

    def __repr__(self):
        return f"BinOp({self.left} {self.op} {self.right})"


class Identifier(ASTNode):
    """A variable reference."""
    def __init__(self, name, line=None):
        self.name = name
        self.line = line

    def __repr__(self):
        return f"ID({self.name})"


class IntLiteral(ASTNode):
    def __init__(self, value, line=None):
        self.value = int(value)
        self.line = line

    def __repr__(self):
        return f"NUM({self.value})"


class StringLiteral(ASTNode):
    def __init__(self, value, line=None):
        self.value = value   # already stripped of quotes
        self.line = line

    def __repr__(self):
        return f'STR("{self.value}")'
