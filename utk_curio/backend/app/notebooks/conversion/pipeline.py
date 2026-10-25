"""Run the notebook-conversion pipeline and return a Curio dataflow spec."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import nbformat

from .analyze_notebooks import analyze_notebook
from .generate_curio_json import graph_to_curio
from .generate_python_files_from_nbs import convert_nb
from .graph_prop_labels import build_graph
from .lib_attribution import analyze


def convert_notebook(notebook: dict[str, Any], name: str) -> dict[str, Any]:
    """Convert notebook JSON into a workflow using the integrated pipeline."""
    if not isinstance(notebook, dict):
        raise ValueError("Notebook must be a JSON object.")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("A notebook name is required.")
    if not isinstance(notebook.get("cells"), list):
        raise ValueError("Notebook cells must be a list.")
    if not isinstance(notebook.get("nbformat"), int):
        raise ValueError("Notebook must include an integer nbformat version.")

    try:
        nbformat.validate(notebook)
    except (nbformat.ValidationError, NotImplementedError) as exc:
        raise ValueError(f"Invalid Jupyter notebook: {exc}") from exc

    with TemporaryDirectory(prefix="curio-notebook-conversion-") as directory:
        notebook_path = Path(directory) / "notebook.ipynb"
        notebook_path.write_text(json.dumps(notebook), encoding="utf-8")

        try:
            code = convert_nb(str(notebook_path))
            _, variable_attribution = analyze(code)
            analysis = analyze_notebook(notebook_path, variable_attribution)
        except (nbformat.ValidationError, NotImplementedError) as exc:
            raise ValueError(f"Invalid Jupyter notebook: {exc}") from exc

    graph = build_graph(analysis)
    return graph_to_curio(graph, name.strip())
