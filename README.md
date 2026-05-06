# MiniLang Compiler

MiniLang is a small educational compiler project with:
- Lexer
- Parser
- Semantic analyzer
- Runtime execution (final variable values)
- Web frontend to visualize tokens, AST, symbols, result, and errors

## Syntax-Directed Checks (SDT/SDD Lite)

This project uses a lightweight syntax-directed approach in the parser while
still building an AST:

- The parser maintains a symbol table and records semantic errors as it parses.
- Expression parsing returns both the AST node and its inferred type.
- Type rules are applied at the point where grammar productions are recognized
  (e.g., when building binary operator nodes).
- Declarations and assignments perform semantic checks immediately during
  parsing (re-declaration, use-before-declare, type mismatch).

In other words, semantic actions are executed during parsing (SDT-style) rather
than only in a separate, later AST walk. The AST is still built for later
phases and debugging, but type checking and symbol table updates are performed
as part of the parsing process.

## Project Structure

- backend: Flask API
- compiler: compiler phases and interpreter
- frontend/static: single-page UI
- tests: unit and integration tests

## Quick Start

1. Install dependencies:

    pip install -r requirements.txt

2. Run backend server:

    python backend/app.py

3. Open in browser:

    http://127.0.0.1:5000/

4. Paste a sample program into the editor and click Run.

## Useful Commands

Run tests:

    python -m pytest tests/ -v

## Frontend Test Programs

### 1) Basic arithmetic + loops (successful run)

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

Expected:
- Errors: 0
- Result: x=10, y=3, result=0, msg="done"

### 2) String concatenation (successful run)

    string first;
    string last;
    string full;

    first = "Ada";
    last = "Lovelace";
    full = first + " " + last;

Expected:
- Errors: 0
- Result includes full="Ada Lovelace"

### 3) Nested blocks and scope usage (successful run)

    int a;
    int b;
    int c;

    a = 2;
    b = 5;
    c = 0;

    if b > a then {
      c = b - a;
      while c > 1 do {
        c = c - 1;
      }
    } else {
      c = a - b;
    }

Expected:
- Errors: 0
- Result includes c=1

### 4) Type mismatch (semantic error)

    int x;
    x = "hello";

Expected:
- Errors tab shows type mismatch
- Result stays empty

### 5) Undeclared variable (semantic error)

    int x;
    y = x + 1;

Expected:
- Errors tab shows undeclared variable
- Result stays empty

### 6) Syntax error (parser error)

    int x
    x = 5;

Expected:
- Errors tab shows missing semicolon / parse error

### 7) Runtime error: division by zero

    int x;
    x = 10 / 0;

Expected:
- Errors tab shows execution error (division by zero)
- Result stays empty

### 8) Line-number stress test (multiline)

    int i;
    int sum;
    i = 1;
    sum = 0;

    while i <= 20 do {
      sum = sum + i;
      i = i + 1;
    }

Expected:
- Line numbers display vertically in gutter
- Result includes sum=210

## API

POST /compile

Request body:

    {
      "source": "int x; x = 5;"
    }

Response body includes:
- success
- tokens
- ast
- symbols
- result
- errors
