# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests for the model classes and their API."""


from invenio_madmp.models import DataManagementPlan, Dataset

# ------->
# Dataset
# ------->


def test_find_dataset_by_id(base_app, example_data):
    dataset = Dataset.get_by_dataset_id("dataset-1")

    assert dataset is not None
    assert dataset.dataset_id == "dataset-1"


def test_find_dataset_by_id_nonexisting(base_app, example_data):
    dataset = Dataset.get_by_dataset_id("non-existing")

    assert dataset is None


def test_find_dataset_by_record(base_app, example_data):
    for record in (ds.record for ds in example_data["datasets"]):
        dataset = Dataset.get_by_record(record)

        assert dataset is not None
        assert dataset.record.id == record.id


def test_find_dataset_by_record_pid(base_app, example_data):
    for record in (ds.record for ds in example_data["datasets"]):
        dataset = Dataset.get_by_record_pid(record.pid)

        assert dataset is not None
        assert dataset.record.id == record.id


def test_find_dataset_by_record_pid_nonexisting(base_app, example_data):
    dataset = Dataset.get_by_record_pid("non-existing-pid")

    assert dataset is None


# --------------------->
# Data Management Plans
# --------------------->


def test_find_dmp_by_id(base_app, example_data):
    dmp = DataManagementPlan.get_by_dmp_id("dmp-2")

    assert dmp is not None
    assert dmp.dmp_id == "dmp-2"


def test_find_dmp_by_id_nonexisting(base_app, example_data):
    dmp = DataManagementPlan.get_by_dmp_id("non-existing")

    assert dmp is None


def test_find_dmps_by_record(base_app, example_data):
    for dataset in example_data["used_datasets"]:
        rec = dataset.record
        dmps = DataManagementPlan.get_by_record(rec)

        assert isinstance(dmps, list)
        assert dmps
        for dmp in dmps:
            assert isinstance(dmp, DataManagementPlan)


def test_find_dmps_by_record_unused(base_app, example_data):
    for rec in example_data["unused_records"]:
        dmps = DataManagementPlan.get_by_record(rec)

        assert isinstance(dmps, list)
        assert not dmps


def test_find_dmps_by_record_pid(base_app, example_data):
    for rec in (ds.record for ds in example_data["used_datasets"]):
        dmps = DataManagementPlan.get_by_record_pid(rec.pid)

        assert isinstance(dmps, list)
        assert dmps
        for dmp in dmps:
            assert isinstance(dmp, DataManagementPlan)


def test_find_dmps_by_record_pid_nonexisting(base_app, example_data):
    dmps = DataManagementPlan.get_by_record_pid("non-existing-pid")

    assert dmps == []


def test_find_dmps_by_record_pid_unused(base_app, example_data):
    for rec in example_data["unused_records"]:
        dmps = DataManagementPlan.get_by_record_pid(rec.pid)

        assert isinstance(dmps, list)
        assert not dmps
