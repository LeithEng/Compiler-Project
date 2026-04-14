"""
tests/test_execution.py — execution/runtime integration tests.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from compiler import compile_source


def result_map(result_rows):
    return {row["name"]: row["value"] for row in result_rows}


def test_execution_result_values():
    src = """
int x;
int y;
int result;
string msg;

x = 10;
y = 3;
result = x + y * 2;

if result > 15 then {
    result = result - 5;
} else {
    result = result + 1;
}

while result > 0 do {
    result = result - 1;
}

msg = "done";
"""
    out = compile_source(src)
    assert out["success"] is True
    assert out["errors"] == []

    values = result_map(out["result"])
    assert values == {
        "x": 10,
        "y": 3,
        "result": 0,
        "msg": "done",
    }


def test_execution_runtime_error_is_reported():
    src = "int x; x = 10 / 0;"
    out = compile_source(src)

    assert out["success"] is False
    assert out["result"] == []
    assert any(e["phase"] == "ExecutionError" for e in out["errors"])
