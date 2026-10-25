from flask import request, jsonify
from utk_curio.backend.app.notebooks import notebooks_bp
from utk_curio.backend.app.notebooks.analyzer import analyze_cells
from utk_curio.backend.app.notebooks.conversion.pipeline import convert_notebook


@notebooks_bp.route('/api/analyzeNotebook', methods=['POST'])
def analyze_notebook():
    cells = request.get_json(force=True).get('cells', [])
    return jsonify(analyze_cells(cells))


@notebooks_bp.route('/api/notebooks/convert', methods=['POST'])
def convert_jupyter_notebook():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    notebook = payload.get("notebook")
    name = payload.get("name")
    if not isinstance(notebook, dict):
        return jsonify({"error": "Notebook must be a JSON object."}), 400
    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "A notebook name is required."}), 400

    try:
        return jsonify(convert_notebook(notebook, name)), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
