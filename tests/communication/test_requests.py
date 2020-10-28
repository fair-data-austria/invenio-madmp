# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests for the outgoing update notifications."""


import json

import httpretty
import pytest
from invenio_pidstore.models import PersistentIdentifier as PID
from requests.exceptions import ConnectionError

from invenio_madmp.comm.requests import (
    _get_record_and_dataset,
    _prepare_endpoint_url,
    send_dataset_addition,
    send_distribution_deletion,
    send_distribution_update,
)

# ------------------------------------------>
# Helper functions for setting up httpretty
# ------------------------------------------>


def _auth_checking_handler(request, uri, response_headers):
    """Handler that checks if Authorization is present."""
    if not request.headers.get("Authorization", "").startswith("Bearer"):
        return 401, response_headers, json.dumps({"error": "not authorized"})

    return 200, response_headers, json.dumps({})


def _no_auth_handler(request, uri, response_headers):
    """Handler that checks if Authorization is absent."""
    if request.headers.get("Authorization"):
        return 400, response_headers, json.dumps({"error": "unexpected auth"})

    return 200, response_headers, json.dumps({})


def _failing_handler(request, uri, response_headers):
    """Handler that imitates a failing connection."""
    raise Exception


def _register_uris(app, request_callback, dataset_id=None, dmp_id=None):
    """Register the URIs with the specified callback via httpretty."""
    if dataset_id is not None:
        for method in [httpretty.POST, httpretty.PATCH, httpretty.DELETE]:
            url = _prepare_endpoint_url(
                app.config["MADMP_DMP_TOOL_DATASET_ENDPOINT_URL"],
                dataset_id,
            )
            httpretty.register_uri(method, url, body=request_callback)
            url = _prepare_endpoint_url(
                app.config["MADMP_DMP_TOOL_DATASETS_ENDPOINT_URL"],
                dataset_id,
            )
            httpretty.register_uri(method, url, body=request_callback)

    if dmp_id is not None:
        for method in [httpretty.POST, httpretty.PATCH, httpretty.DELETE]:
            url = _prepare_endpoint_url(
                app.config["MADMP_DMP_TOOL_DMP_ENDPOINT_URL"],
                dmp_id,
            )
            httpretty.register_uri(method, url, body=request_callback)
            url = _prepare_endpoint_url(
                app.config["MADMP_DMP_TOOL_DMPS_ENDPOINT_URL"],
                dmp_id,
            )
            httpretty.register_uri(method, url, body=request_callback)


# ----------------------------->
# sending update notifications
# ----------------------------->
# distribution update
# -------------------->


@httpretty.activate
def test_send_distribution_update(base_app, example_data):
    """Check if send_distribution_update works as expected under normal conditions."""
    dataset = example_data["datasets"][0]
    _register_uris(base_app, _auth_checking_handler, dataset_id=dataset.dataset_id)
    result = send_distribution_update(dataset=dataset)
    assert result


@httpretty.activate
def test_send_distribution_update_no_auth(base_app, example_data):
    """Check if the bearer token is omitted from the header if set to None."""
    base_app.config["MADMP_COMMUNICATION_TOKEN"] = None
    dataset = example_data["datasets"][0]
    _register_uris(base_app, _no_auth_handler, dataset_id=dataset.dataset_id)
    result = send_distribution_update(dataset=dataset)
    assert result


@httpretty.activate
def test_send_distribution_update_silent_connection_failure(base_app, example_data):
    """Check if raise_exc=False really suppresses exceptions."""
    dataset = example_data["datasets"][0]
    _register_uris(base_app, _failing_handler, dataset_id=dataset.dataset_id)
    result = send_distribution_update(dataset=dataset, raise_exc=False)
    assert not result


@httpretty.activate
def test_send_distribution_update_connection_failure(base_app, example_data):
    dataset = example_data["datasets"][0]
    _register_uris(base_app, _failing_handler, dataset_id=dataset.dataset_id)
    with pytest.raises(ConnectionError):
        send_distribution_update(dataset=dataset, raise_exc=True)


def test_send_distribution_update_no_data():
    res = send_distribution_update()
    assert not res


# ---------------------->
# distribution deletion
# ---------------------->


@httpretty.activate
def test_send_distribution_deletion(base_app, example_data):
    """Check if send_distribution_update works as expected under normal conditions."""
    dataset = example_data["datasets"][0]
    _register_uris(base_app, _auth_checking_handler, dataset_id=dataset.dataset_id)
    result = send_distribution_deletion(dataset=dataset)
    assert result


@httpretty.activate
def test_send_distribution_deletion_no_auth(base_app, example_data):
    """Check if the bearer token is omitted from the header if set to None."""
    base_app.config["MADMP_COMMUNICATION_TOKEN"] = None
    dataset = example_data["datasets"][0]
    _register_uris(base_app, _no_auth_handler, dataset_id=dataset.dataset_id)
    result = send_distribution_deletion(dataset=dataset)
    assert result


@httpretty.activate
def test_send_distribution_deletion_silent_connection_failure(base_app, example_data):
    """Check if raise_exc=False really suppresses exceptions."""
    dataset = example_data["datasets"][0]
    _register_uris(base_app, _failing_handler, dataset_id=dataset.dataset_id)
    result = send_distribution_deletion(dataset=dataset, raise_exc=False)
    assert not result


@httpretty.activate
def test_send_distribution_deletion_connection_failure(base_app, example_data):
    dataset = example_data["datasets"][0]
    _register_uris(base_app, _failing_handler, dataset_id=dataset.dataset_id)
    with pytest.raises(ConnectionError):
        send_distribution_deletion(dataset=dataset, raise_exc=True)


def test_send_distribution_deletion_no_data():
    res = send_distribution_deletion()
    assert not res


# ----------------->
# dataset addition
# ----------------->


@httpretty.activate
def test_send_dataset_addition(base_app, example_data):
    """Check if send_distribution_update works as expected under normal conditions."""
    dataset = example_data["datasets"][0]
    dmp = dataset.dmps[0]
    dmp_id = dmp.dmp_id
    _register_uris(
        base_app, _auth_checking_handler, dataset_id=dataset.dataset_id, dmp_id=dmp_id
    )
    result = send_dataset_addition(dmp=dmp, dataset=dataset)
    assert result


@httpretty.activate
def test_send_dataset_addition_no_auth(base_app, example_data):
    """Check if the bearer token is omitted from the header if set to None."""
    base_app.config["MADMP_COMMUNICATION_TOKEN"] = None
    dataset = example_data["datasets"][0]
    dmp = dataset.dmps[0]
    _register_uris(
        base_app, _no_auth_handler, dataset_id=dataset.dataset_id, dmp_id=dmp.dmp_id
    )
    result = send_dataset_addition(dmp=dmp, dataset=dataset)
    assert result


@httpretty.activate
def test_send_dataset_addition_silent_connection_failure(base_app, example_data):
    """Check if raise_exc=False really suppresses exceptions."""
    dataset = example_data["datasets"][0]
    dmp = dataset.dmps[0]
    _register_uris(
        base_app, _failing_handler, dataset_id=dataset.dataset_id, dmp_id=dmp.dmp_id
    )
    result = send_dataset_addition(dmp=dmp, dataset=dataset, raise_exc=False)
    assert not result


@httpretty.activate
def test_send_dataset_addition_connection_failure(base_app, example_data):
    dataset = example_data["datasets"][0]
    dmp = dataset.dmps[0]
    _register_uris(
        base_app, _failing_handler, dataset_id=dataset.dataset_id, dmp_id=dmp.dmp_id
    )
    with pytest.raises(ConnectionError):
        send_dataset_addition(dmp=dmp, dataset=dataset, raise_exc=True)


def test_send_dataset_addition_no_data():
    res = send_dataset_addition()
    assert not res


# ------------------------>
# _get_record_and_dataset
# ------------------------>
#
# check if the various ways of fetching records/datasets work
#


def test_get_record_and_dataset_by_record(example_data):
    dataset = example_data["datasets"][0]
    record = dataset.record
    rec, ds = _get_record_and_dataset(record=record)
    assert ds == dataset
    assert rec == record


def test_get_record_and_dataset_by_record_uuid(example_data):
    dataset = example_data["datasets"][0]
    record = dataset.record
    rec, ds = _get_record_and_dataset(record_uuid=record.id)
    assert ds == dataset
    assert rec == record


def test_get_record_and_dataset_by_record_pid(example_data):
    dataset = example_data["datasets"][0]
    record = dataset.record
    pid = PID.query.filter(PID.object_uuid == record.id).first()
    rec, ds = _get_record_and_dataset(pid_object=pid)
    assert ds == dataset
    assert rec == record


def test_get_record_and_dataset_by_record_pid_value(example_data):
    dataset = example_data["datasets"][0]
    record = dataset.record
    pid = PID.query.filter(PID.object_uuid == record.id).first()
    rec, ds = _get_record_and_dataset(pid_value=pid.pid_value)
    assert ds == dataset
    assert rec == record


def test_get_record_and_dataset_by_dataset(example_data):
    dataset = example_data["datasets"][0]
    record = dataset.record
    rec, ds = _get_record_and_dataset(dataset=dataset)
    assert ds == dataset
    assert rec == record


def test_get_record_and_dataset_by_dataset_id(example_data):
    dataset = example_data["datasets"][0]
    record = dataset.record
    rec, ds = _get_record_and_dataset(dataset_id=dataset.dataset_id)
    assert ds == dataset
    assert rec == record


def test_get_record_and_dataset_by_multiple_values(example_data):
    dataset = example_data["datasets"][0]
    record = dataset.record
    pid = PID.query.filter(PID.object_uuid == record.id).first()
    rec, ds = _get_record_and_dataset(
        record=record,
        record_uuid=record.id,
        dataset=dataset,
        dataset_id=dataset.dataset_id,
        pid_object=pid,
        pid_value=pid.pid_value,
    )
    assert ds == dataset
    assert rec == record


def test_get_record_and_dataset_no_data():
    res = _get_record_and_dataset()
    assert not res
