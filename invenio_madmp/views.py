"""Blueprint definitions for maDMP integration."""

from flask import Blueprint, jsonify, request
from invenio_db import db

from .convert import convert_dmp
from .models import DataManagementPlan

rest_blueprint = Blueprint(
    "invenio_madmp",
    __name__,
)


def _summarize_dmp(dmp: DataManagementPlan) -> dict:
    """Create a summary dictionary for the given DMP."""
    res = {"dmp_id": dmp.dmp_id, "datasets": []}

    for ds in dmp.datasets:
        dataset = {"dataset_id": ds.dataset_id, "record": None}

        if ds.record:
            dataset["record"] = ds.record.model.json

        res["datasets"].append(dataset)

    return res


@rest_blueprint.route("/dmps", methods=["GET"])
def list_dmps():
    """Give a summary of all stored DMPs."""
    dmps = DataManagementPlan.query.all()
    res = [_summarize_dmp(dmp) for dmp in dmps]

    return jsonify(res)


@rest_blueprint.route("/dmps", methods=["POST"])
def create_dmp():
    """Create a new DMP from the maDMP JSON in the request body."""
    if request.json is None:
        return jsonify({"error": "no json body supplied"}), 400
    elif request.json.get("dmp") is None:
        return jsonify({"error": "dmp not found in the body"}), 400

    dmp_json = request.json.get("dmp", {})
    dmp_json_id = dmp_json.get("dmp_id", {}).get("identifier")

    if DataManagementPlan.get_by_dmp_id(dmp_json_id) is not None:
        return jsonify({"error": "dmp with the same id already exists"}), 409

    dmp = convert_dmp(dmp_json)
    db.session.add(dmp)
    db.session.commit()

    # TODO change the returned value
    return jsonify(_summarize_dmp(dmp)), 201


@rest_blueprint.route("/dmps/<dmp_id>", methods=["PATCH"])
def update_dmp(dmp_id: str = None):
    """Update the specified DMP using the maDMP JSON in the request body."""
    hard_sync = request.args.get("sync", "soft") == "hard"

    if request.json is None:
        return jsonify({"error": "no json body supplied"}), 400
    elif request.json.get("dmp") is None:
        return jsonify({"error": "dmp not found in the body"}), 400

    dmp_json = request.json.get("dmp", {})
    dmp_json_id = dmp_json.get("dmp_id", {}).get("identifier")

    if dmp_id and dmp_json_id and dmp_id != dmp_json_id:
        return jsonify({"error": "mismatch between dmp id from url and body"}), 400

    dmp_id = dmp_id or dmp_json_id
    if DataManagementPlan.get_by_dmp_id(dmp_id) is None:
        return jsonify({"error": "dmp not found"}), 404

    dmp = convert_dmp(dmp_json, hard_sync)
    db.session.commit()

    # TODO change the returned value
    return jsonify(_summarize_dmp(dmp))


@rest_blueprint.route("/dmps", methods=["PATCH"])
def update_dmp_without_id():
    """Update the specified DMP using the maDMP JSON in the request body."""
    return update_dmp(None)
