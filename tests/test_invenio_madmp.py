# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

import pytest
from flask import Flask
from invenio_accounts.models import User
from invenio_pidstore.models import PersistentIdentifier as PID

from invenio_madmp import InvenioMaDMP
from invenio_madmp.convert import convert_dmp
from invenio_madmp.models import DataManagementPlan, Dataset


def test_version():
    """Test version import."""
    from invenio_madmp import __version__

    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask("testapp")
    ext = InvenioMaDMP(app)
    assert "invenio-madmp" in app.extensions

    app = Flask("testapp")
    ext = InvenioMaDMP()
    assert "invenio-madmp" not in app.extensions
    ext.init_app(app)
    assert "invenio-madmp" in app.extensions


# ====== #
# Models #
# ====== #

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
        rec_pid = PID.get_by_object("recid", "rec", record.id)
        dataset = Dataset.get_by_record_pid(rec_pid)

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
        rec_pid = PID.get_by_object("recid", "rec", rec.id)
        dmps = DataManagementPlan.get_by_record_pid(rec_pid)

        assert isinstance(dmps, list)
        assert dmps
        for dmp in dmps:
            assert isinstance(dmp, DataManagementPlan)


def test_find_dmps_by_record_pid_nonexisting(base_app, example_data):
    dmps = DataManagementPlan.get_by_record_pid("non-existing-pid")

    assert dmps == []


def test_find_dmps_by_record_pid_unused(base_app, example_data):
    for rec in example_data["unused_records"]:
        rec_pid = PID.get_by_object("recid", "rec", rec.id)
        dmps = DataManagementPlan.get_by_record_pid(rec_pid)

        assert isinstance(dmps, list)
        assert not dmps


# ========== #
# Conversion #
# ========== #


def test_successful_conversion(
    base_app, example_madmps_for_invenio, all_required_accounts
):
    for _, madmp in example_madmps_for_invenio.items():
        dmp = convert_dmp(madmp["dmp"])

        assert dmp is not None
        assert dmp.dmp_id == madmp["dmp"]["dmp_id"]["identifier"]


def test_no_users(base_app, example_madmps_for_invenio_requiring_users):
    assert len(User.query.all()) == 0

    problematic_madmps = example_madmps_for_invenio_requiring_users
    for madmp in problematic_madmps:
        with pytest.raises(LookupError):
            madmp = problematic_madmps[madmp]["dmp"]
            convert_dmp(madmp)
