"""
backend/app.py — Flask API server
Exposes POST /compile  →  JSON result from the compiler pipeline.
Run with:  python backend/app.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask, request, jsonify
from flask_cors import CORS
from compiler import compile_source

app = Flask(__name__, static_folder="../frontend/static", static_url_path="/static")
CORS(app)


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/compile", methods=["POST"])
def compile_endpoint():
    data = request.get_json(force=True)
    source = data.get("source", "")
    if not source.strip():
        return jsonify({"success": False, "errors": [
            {"phase": "input", "line": None, "message": "No source code provided."}
        ], "tokens": [], "ast": None, "symbols": [], "result": []}), 400

    result = compile_source(source)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
