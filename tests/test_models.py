# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests for the model classes and their API."""


from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier as PID

from invenio_madmp.models import DataManagementPlan, Dataset

# ------->
# Dataset
# ------->


def test_find_dataset_by_id(example_data):
    dataset = Dataset.get_by_dataset_id("dataset-1")

    assert dataset is not None
    assert dataset.dataset_id == "dataset-1"


def test_find_dataset_by_id_nonexisting(example_data):
    dataset = Dataset.get_by_dataset_id("non-existing")

    assert dataset is None


def test_find_dataset_by_record(example_data):
    for record in (ds.record for ds in example_data["datasets"]):
        dataset = Dataset.get_by_record(record)

        assert dataset is not None
        assert dataset.record.id == record.id


def test_find_dataset_by_record_pid(example_data):
    for record in (ds.record for ds in example_data["datasets"]):
        pid = PID.query.filter(PID.object_uuid == record.id).first()
        dataset = Dataset.get_by_record_pid(pid)

        assert dataset is not None
        assert dataset.record.id == record.id


def test_find_dataset_by_record_pid_nonexisting(example_data):
    dataset = Dataset.get_by_record_pid("non-existing-pid")

    assert dataset is None


def test_has_record(example_data):
    for dataset in example_data["datasets"]:
        assert dataset.record is not None
        assert dataset.has_record


def test_has_record_none_assigned(example_data):
    ds = Dataset.create("unassigned dataset", None)
    assert ds.record is None
    assert not ds.has_record


def test_set_record(example_data):
    ds = example_data["datasets"][0]
    old_record = ds.record
    new_record = example_data["unused_records"][0]
    new_pid = PID.query.filter(PID.object_uuid == new_record.id).first()

    ds.record = new_record
    assert ds.record == new_record
    assert ds.record_pid == new_pid
    assert ds.record_pid_id == new_pid.id
    assert old_record != new_record


def test_delete_dataset(example_data):
    dataset = example_data["datasets"][0]
    assert dataset in db.session

    dataset.delete()
    assert dataset not in db.session


# --------------------->
# Data Management Plans
# --------------------->


def test_find_dmp_by_id(example_data):
    dmp = DataManagementPlan.get_by_dmp_id("dmp-2")

    assert dmp is not None
    assert dmp.dmp_id == "dmp-2"


def test_find_dmp_by_id_nonexisting(example_data):
    dmp = DataManagementPlan.get_by_dmp_id("non-existing")

    assert dmp is None


def test_find_dmps_by_record(example_data):
    for dataset in example_data["used_datasets"]:
        rec = dataset.record
        dmps = DataManagementPlan.get_by_record(rec)

        assert isinstance(dmps, list)
        assert dmps
        for dmp in dmps:
            assert isinstance(dmp, DataManagementPlan)


def test_find_dmps_by_record_unused(example_data):
    for rec in example_data["unused_records"]:
        dmps = DataManagementPlan.get_by_record(rec)

        assert isinstance(dmps, list)
        assert not dmps


def test_find_dmps_by_record_pid(example_data):
    for rec in (ds.record for ds in example_data["used_datasets"]):
        pid = PID.query.filter(PID.object_uuid == rec.id).first()
        dmps = DataManagementPlan.get_by_record_pid(pid)

        assert isinstance(dmps, list)
        assert dmps
        for dmp in dmps:
            assert isinstance(dmp, DataManagementPlan)


def test_find_dmps_by_record_pid_nonexisting(example_data):
    dmps = DataManagementPlan.get_by_record_pid("non-existing-pid")

    assert dmps == []


def test_find_dmps_by_record_pid_unused(example_data):
    for rec in example_data["unused_records"]:
        pid = PID.query.filter(PID.object_uuid == rec.id).first()
        dmps = DataManagementPlan.get_by_record_pid(pid)

        assert isinstance(dmps, list)
        assert not dmps


def test_add_dataset(example_data):
    dmp = example_data["dmps"][0]
    dataset = example_data["unused_datasets"][0]

    assert dataset not in dmp.datasets

    old_len = len(dmp.datasets)
    result = dmp.add_dataset(dataset)

    assert result
    assert (old_len + 1) == len(dmp.datasets)
    assert dataset in dmp.datasets


def test_add_dataset_already_included(example_data):
    dmp = example_data["dmps"][0]
    dataset = dmp.datasets[0]

    assert dataset in dmp.datasets

    old_len = len(dmp.datasets)
    result = dmp.add_dataset(dataset)

    assert not result
    assert old_len == len(dmp.datasets)
    assert dataset in dmp.datasets


def test_remove_dataset(example_data):
    dmp = example_data["dmps"][0]

    for dataset in dmp.datasets.copy():
        assert dataset in dmp.datasets
        result = dmp.remove_dataset(dataset)
        assert result
        assert dataset not in dmp.datasets

    assert not dmp.datasets


def test_remove_dataset_not_included(example_data):
    dmp = example_data["dmps"][0]
    dataset = example_data["unused_datasets"][0]
    old_len = len(dmp.datasets)

    result = dmp.remove_dataset(dataset)

    assert not result
    assert len(dmp.datasets) == old_len


def test_delete_dmp(example_data):
    dmp = example_data["dmps"][0]
    assert dmp in db.session

    dmp.delete()
    assert dmp not in db.session
