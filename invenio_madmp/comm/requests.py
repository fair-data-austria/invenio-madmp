"""TODO."""

import json
import re
from typing import Optional, Tuple
from uuid import UUID

import requests
from flask import current_app as app
from invenio_pidstore.models import PersistentIdentifier as PID
from invenio_records.api import Record
from sqlalchemy.orm.exc import NoResultFound

from ..convert.util import convert_record
from ..models import DataManagementPlan, Dataset

# ------- #
# Helpers #
# ------- #


def _prepare_endpoint_url(url: str, obj_id: str) -> str:
    """Replace the placeholder (if present) in the URL string with the object's ID."""
    if "%s" in url:
        return url % obj_id
    elif "{}" in url:
        return url.format(obj_id)
    else:
        return url


def _prepare_headers() -> dict:
    """Prepare additional HTTP headers for the requests."""
    headers = {
        "Content-Type": "application/json"
    }

    if app.config["MADMP_COMMUNICATION_TOKEN"] is not None:
        headers["Authorization"] = "Bearer %s" % app.config["MADMP_COMMUNICATION_TOKEN"]

    return headers


def _get_record_and_dataset(
    record: Record = None,
    record_uuid: UUID = None,
    dataset: Dataset = None,
    dataset_id: str = None,
    pid_object: PID = None,
    pid_value: str = None,
) -> Optional[Tuple[Record, Dataset]]:
    """Try to find the dataset and record matching the given hints."""
    try:
        rec = record or Record.get_record(record_uuid)  # TODO: what about drafts?
    except NoResultFound:
        rec = None
    ds = None

    if rec is None:
        ds = dataset or Dataset.get_by_dataset_id(dataset_id)
        if ds is not None:
            rec = ds.record

    if rec is None:
        pid = pid_object or PID.query.filter(PID.pid_value == pid_value).first()
        if pid:
            # we're going over the Dataset because it queries both records and drafts,
            # and we don't want to send updates for records that aren't associated with
            # some dataset anyways
            ds = Dataset.get_by_record_pid(pid)
            if ds:
                rec = ds.record

    if rec is None:
        return None
    else:
        ds = ds or Dataset.get_by_record(rec)
        return (rec, ds)


def _send_distribution_notification(
    record: Record, dataset: Dataset, notification_type: str = "update"
) -> bool:
    """The common logic for sending dataset updates to the DMP tool."""
    if notification_type not in ["update", "delete"]:
        raise ValueError("invalid notification type: %s" % notification_type)

    dataset_body = convert_record(record)
    if not dataset_body and notification_type == "update":
        return False

    # TODO dataset_id will be replaced by a list
    specific_url = app.config["MADMP_DMP_TOOL_DATASET_ENDPOINT_URL"]
    generic_url = app.config["MADMP_DMP_TOOL_DATASETS_ENDPOINT_URL"]
    if re.match(r"[\w\-\.]+", dataset.dataset_id):
        # if the dataset_id is simple enough, we'll use it in the URL
        endpoint_url = _prepare_endpoint_url(specific_url, dataset.dataset_id)
    else:
        # if it may cause issues, we'll specify it in the body
        endpoint_url = generic_url
        if not dataset_body.get("dataset_id"):
            return False

    headers = _prepare_headers()
    dataset_body_json = json.dumps(dataset_body)
    if notification_type == "update":
        resp = requests.patch(endpoint_url, data=dataset_body_json, headers=headers)
    elif notification_type == "delete":
        resp = requests.delete(endpoint_url, data=dataset_body_json, headers=headers)

    if 200 <= resp.status_code < 300:
        return True
    else:
        return False


def _send_dmp_notification(dmp: DataManagementPlan, dataset: Dataset) -> bool:
    """The common logic for sending DMP updates to the DMP tool."""
    dataset_body = convert_record(dataset.record)

    specific_url = app.config["MADMP_DMP_TOOL_DMP_ENDPOINT_URL"]
    endpoint_url = _prepare_endpoint_url(specific_url, dataset.dataset_id)

    headers = _prepare_headers()
    dataset_body_json = json.dumps(dataset_body)
    resp = requests.post(endpoint_url, data=dataset_body_json, headers=headers)

    # TODO it's planned that this request will return a dataset_id that should be used
    #      for future communication regarding the dataset

    if 200 <= resp.status_code < 300:
        return True
    else:
        return False


# === #
# API #
# === #


def send_distribution_update(
    record: Record = None,
    record_uuid: UUID = None,
    dataset: Dataset = None,
    dataset_id: str = None,
    pid_object: PID = None,
    pid_value: str = None,
) -> bool:
    """TODO."""
    res = _get_record_and_dataset(
        record, record_uuid, dataset, dataset_id, pid_object, pid_value
    )

    if res is None:
        return False
    else:
        rec, ds = res
        return _send_distribution_notification(rec, ds, notification_type="update")


def send_distribution_deletion(
    record: Record = None,
    record_uuid: UUID = None,
    dataset: Dataset = None,
    dataset_id: str = None,
    pid_object: PID = None,
    pid_value: str = None,
) -> bool:
    """TODO."""
    res = _get_record_and_dataset(
        record, record_uuid, dataset, dataset_id, pid_object, pid_value
    )

    if res is None:
        return False
    else:
        rec, ds = res
        return _send_distribution_notification(rec, ds, notification_type="delete")


def send_dataset_addition(
    dmp: DataManagementPlan = None,
    dmp_id: str = None,
    record: Record = None,
    record_uuid: UUID = None,
    dataset: Dataset = None,
    dataset_id: str = None,
    pid_object: PID = None,
    pid_value: str = None,
) -> bool:
    """TODO."""
    if dmp is None:
        if dmp_id is None:
            return False
        else:
            dmp = DataManagementPlan.get_by_dmp_id(dmp_id)

    if dmp is None:
        return False
    else:
        res = _get_record_and_dataset(
            record, record_uuid, dataset, dataset_id, pid_object, pid_value
        )

    if res is None:
        return False
    else:
        rec, ds = res
        return _send_dmp_notification(dmp, ds)
