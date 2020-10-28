# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests checking if the default signal handlers (aka observers) work as intended."""


import unittest.mock as mock

from invenio_pidstore.models import PersistentIdentifier as PID
from invenio_records.signals import after_record_delete, after_record_update

from invenio_madmp.models import DataManagementPlan, Dataset
from invenio_madmp.signals import (
    dataset_deleted,
    dataset_record_pid_changed,
    dmp_dataset_added,
)

# ------------------------------>
# Signal Emmission by API Calls
# ------------------------------>
#
# check if calling the appropriate functions/methods causes signals to be emitted
# (with the default configuration), which should cause notifications to be sent to
# the DMP tool in turn
#


@mock.patch("invenio_madmp.comm.observers.send_dataset_addition")
def test_prepare_sending_new_dataset_by_api(mock_func, example_data):
    rec = example_data["unused_records"][0]
    ds = Dataset.create("dataset", rec.pid)
    dmp = DataManagementPlan.create("dmp", [])
    dmp.add_dataset(ds)
    mock_func.assert_called_once_with(dmp=dmp, dataset=ds, raise_exc=False)


@mock.patch("invenio_madmp.comm.observers.send_distribution_deletion")
def test_prepare_sending_deleted_dataset_by_api(mock_func, example_data):
    ds = example_data["datasets"][0]
    ds.delete()
    mock_func.assert_called_once_with(dataset=ds, raise_exc=False)


@mock.patch("invenio_madmp.comm.observers.send_distribution_deletion")
def test_prepare_sending_distribution_deletion_by_api(mock_func, example_data):
    ds = example_data["datasets"][0]
    rec = ds.record
    rec.delete()
    mock_func.assert_called_once_with(record=rec, raise_exc=False)


@mock.patch("invenio_madmp.comm.observers.send_distribution_update")
def test_prepare_sending_changed_dataset_by_api(mock_func, example_data):
    ds = example_data["datasets"][0]
    rec = example_data["unused_records"][0]
    ds.record = rec
    mock_func.assert_called_once_with(dataset=ds, raise_exc=False)


@mock.patch("invenio_madmp.comm.observers.send_distribution_update")
def test_prepare_sending_distribution_update_by_api(mock_func, example_data):
    ds = example_data["datasets"][0]
    rec = ds.record
    rec.commit()
    mock_func.assert_called_once_with(dataset=ds, raise_exc=False)


# ------------------------>
# Manual Signal Emmission
# ------------------------>
#
# check if the manual emmission of signals causes notifications to be sent to the
# DMP tool
#


@mock.patch("invenio_madmp.comm.observers.send_distribution_update")
def test_prepare_sending_distribution_update_by_manual_signal(mock_func, example_data):
    ds = example_data["datasets"][0]
    after_record_update.send(None, record=ds.record)
    mock_func.assert_called_once_with(dataset=ds, raise_exc=False)


@mock.patch("invenio_madmp.comm.observers.send_dataset_addition")
def test_prepare_sending_new_dataset_by_manual_signal(mock_func, example_data):
    ds = example_data["datasets"][0]
    dmp = ds.dmps[0]
    dmp_dataset_added.send(None, dmp=dmp, dataset=ds)
    mock_func.assert_called_once_with(dmp=dmp, dataset=ds, raise_exc=False)


@mock.patch("invenio_madmp.comm.observers.send_distribution_deletion")
def test_prepare_sending_deleted_dataset_by_manual_signal(mock_func, example_data):
    ds = example_data["datasets"][0]
    dataset_deleted.send(None, dataset=ds)
    mock_func.assert_called_once_with(dataset=ds, raise_exc=False)


@mock.patch("invenio_madmp.comm.observers.send_distribution_deletion")
def test_prepare_sending_distribution_deletion_by_manual_signal(mock_fn, example_data):
    ds = example_data["datasets"][0]
    rec = ds.record
    after_record_delete.send(None, record=rec)
    mock_fn.assert_called_once_with(record=rec, raise_exc=False)


@mock.patch("invenio_madmp.comm.observers.send_distribution_update")
def test_prepare_sending_changed_dataset_by_manual_signal(mock_func, example_data):
    ds = example_data["datasets"][0]
    rec = example_data["unused_records"][0]
    new_pid = PID.query.filter(PID.object_uuid == rec.id).first()
    old_pid = PID.query.filter(PID.object_uuid == ds.record.id).first()

    dataset_record_pid_changed.send(
        None,
        dataset=ds,
        new_record=rec,
        new_pid=new_pid,
        old_record=ds.record,
        old_pid=old_pid,
    )
    mock_func.assert_called_once_with(dataset=ds, raise_exc=False)
