"""Blueprint definitions for maDMP integration."""

from flask import Blueprint, jsonify, request

from .converters import convert
from .models import DataManagementPlan

rest_blueprint = Blueprint(
    "invenio_madmp",
    __name__,
)


def _summarize_dmp(dmp: DataManagementPlan) -> dict:
    """Create a summary dictionary for the given DMP."""
    res = {
        "dmp_id": dmp.dmp_id,
        "datasets": []
    }

    for ds in dmp.datasets:
        dataset = {
            "dataset_id": ds.dataset_id,
            "record": None
        }

        if ds.record:
            dataset["record"] = ds.record.model.json

        res["datasets"].append(dataset)

    return res


@rest_blueprint.route("/dmps", methods=["POST"])
def create_dmp():
    """Create a new DMP from the maDMP JSON in the request body."""
    dmp_json = request.json.get("dmp", {})
    dmp = convert(dmp_json)
    res = _summarize_dmp(dmp)

    return jsonify(res)


@rest_blueprint.route("/dmps", methods=["GET"])
def list_dmps():
    """Give a summary of all stored DMPs."""
    dmps = DataManagementPlan.query.all()
    res = [_summarize_dmp(dmp) for dmp in dmps]

    return jsonify(res)
