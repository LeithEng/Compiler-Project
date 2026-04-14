"""
symbol_table.py — Symbol table used by the semantic analyzer.
Supports nested scopes so it can be extended for functions later.
"""


class Symbol:
    def __init__(self, name, var_type, line=None):
        self.name = name
        self.var_type = var_type   # 'int' | 'string'
        self.line = line

    def __repr__(self):
        return f"Symbol({self.name}: {self.var_type})"


class SymbolTable:
    """
    A simple scoped symbol table.
    Symbols are looked up from inner scope outward.
    """

    def __init__(self, parent=None):
        self._table: dict[str, Symbol] = {}
        self.parent: "SymbolTable | None" = parent

    # ── Public API ────────────────────────────────────────────────────────────

    def declare(self, name: str, var_type: str, line=None) -> bool:
        """
        Declare a new symbol in the *current* scope.
        Returns False if already declared in this scope (duplicate).
        """
        if name in self._table:
            return False
        self._table[name] = Symbol(name, var_type, line)
        return True

    def lookup(self, name: str) -> "Symbol | None":
        """Search this scope then parent scopes; return Symbol or None."""
        if name in self._table:
            return self._table[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def enter_scope(self) -> "SymbolTable":
        """Create and return a child scope."""
        return SymbolTable(parent=self)

    def all_symbols(self) -> list:
        """Return all symbols in *this* scope (not parents)."""
        return list(self._table.values())

    def to_list(self) -> list[dict]:
        """Serialise to a list of dicts for the JSON API response."""
        rows = []
        for sym in self._table.values():
            rows.append({
                "name": sym.name,
                "type": sym.var_type,
                "line": sym.line,
            })
        return rows

    def __repr__(self):
        return f"SymbolTable({list(self._table.keys())})"
