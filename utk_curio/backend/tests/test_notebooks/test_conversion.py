"""The imported conversion pipeline's API contract."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator


def test_convert_notebook_creates_a_curio_workflow(client):
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "id": "cell-one",
                "source": "values = [1, 2, 3]",
                "metadata": {},
                "execution_count": 1,
                "outputs": [],
            },
            {
                "cell_type": "code",
                "id": "cell-two",
                "source": "total = sum(values)",
                "metadata": {},
                "execution_count": 2,
                "outputs": [],
            },
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    response = client.post(
        "/api/notebooks/convert",
        json={"notebook": notebook, "name": "sample"},
    )

    assert response.status_code == 200
    dataflow = response.get_json()["dataflow"]
    assert dataflow["name"] == "sample"
    assert isinstance(dataflow["timestamp"], int)
    assert dataflow["provenance_id"] == "sample"
    assert len(dataflow["nodes"]) == 2
    assert len(dataflow["edges"]) == 1
    assert dataflow["nodes"][0]["content"].startswith("values =")
    schema_path = Path(__file__).resolve().parents[4] / "docs/schemas/trill.v1.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(response.get_json())


def test_convert_notebook_preserves_branching_cell_dependencies(client):
    sources = [
        "import pandas as pd\nimport numpy as np\n\ndf = pd.read_csv('schools.csv')\ndf",
        "HS_only = df[df['grade'] == 'HS']",
        "MS_only = df[df['grade'] == 'MS']",
        "ES_only = df[df['grade'] == 'ES']",
        "community_zipcode = HS_only[['area', 'zip']]\ngrouped_data = community_zipcode.groupby('area').size().reset_index(name='High School Count')\ngrouped_data",
        "community_zipcode = MS_only[['area', 'zip']]\ngrouped_data = community_zipcode.groupby('area').size().reset_index(name='Middle School Count')\ngrouped_data",
        "community_zipcode = ES_only[['area', 'zip']]\ngrouped_data = community_zipcode.groupby('area').size().reset_index(name='Elementary School Count')\ngrouped_data",
    ]
    notebook = {
        "cells": [
            {
                "cell_type": "code",
                "id": f"cell-{index}",
                "source": source,
                "metadata": {},
                "execution_count": None,
                "outputs": [],
            }
            for index, source in enumerate(sources)
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    response = client.post(
        "/api/notebooks/convert",
        json={"notebook": notebook, "name": "branching"},
    )

    assert response.status_code == 200
    dataflow = response.get_json()["dataflow"]
    assert len(dataflow["nodes"]) == 7
    assert len(dataflow["edges"]) == 6
    edge_pairs = {
        (
            next(i for i, node in enumerate(dataflow["nodes"]) if node["id"] == edge["source"]),
            next(i for i, node in enumerate(dataflow["nodes"]) if node["id"] == edge["target"]),
        )
        for edge in dataflow["edges"]
    }
    assert edge_pairs == {
        (0, 1), (0, 2), (0, 3),
        (1, 4), (2, 5), (3, 6),
    }
    assert [(node["x"], node["y"]) for node in dataflow["nodes"]] == [
        (0, 0),
        (500, 0),
        (500, 300),
        (500, 600),
        (1000, 0),
        (1000, 300),
        (1000, 600),
    ]
    assert "HS_only = arg" in dataflow["nodes"][4]["content"]
    assert "MS_only = arg" in dataflow["nodes"][5]["content"]
    assert "ES_only = arg" in dataflow["nodes"][6]["content"]


def test_convert_notebook_rejects_invalid_notebook(client):
    response = client.post(
        "/api/notebooks/convert",
        json={
            "notebook": {
                "cells": "not a list",
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            },
            "name": "invalid",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Notebook cells must be a list."


def test_convert_notebook_reports_invalid_cell_schema(client):
    response = client.post(
        "/api/notebooks/convert",
        json={
            "notebook": {
                "cells": [{"id": "invalid-cell"}],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            },
            "name": "invalid",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"].startswith("Invalid Jupyter notebook:")


def test_convert_notebook_requires_name(client):
    response = client.post(
        "/api/notebooks/convert",
        json={"notebook": {"cells": []}},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "A notebook name is required."
