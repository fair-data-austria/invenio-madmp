# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests for record converters."""


from flask_principal import Identity
from invenio_access import any_user

from invenio_madmp.convert.records.rdm_records import RDMRecordConverter

# --------------------->
# RDM Record Converter
# --------------------->


def test_matches_dataset(app, example_madmps_for_invenio_with_datacite_metadata):
    """Check that positive suitability (based on metadata schemas) checks work."""
    converter = RDMRecordConverter()
    for dmp in example_madmps_for_invenio_with_datacite_metadata.values():
        for ds in dmp["dmp"].get("dataset", []):
            if ds.get("metadata", []):
                result = converter.matches_dataset(ds, dmp)
                assert result


def test_matches_dataset_different_metadata_schema(
    app, example_madmps_for_invenio
):
    """Check that negative suitability (based on metadata schemas) checks work."""
    converter = RDMRecordConverter()
    for dmp in example_madmps_for_invenio.values():
        for ds in dmp["dmp"].get("dataset", []):
            if ds.get("metadata", []):
                result = converter.matches_dataset(ds, dmp)
                assert not result


def test_matches_record(app, example_data):
    converter = RDMRecordConverter()
    record = example_data["records"][0]
    result = converter.matches_record(record)
    assert result


def test_matches_record_different_type(app):
    """Check if the record converter notices that a wrong object type doesn't fit."""
    converter = RDMRecordConverter()
    result = converter.matches_record("not a record")
    assert not result


def test_update_record(app, example_data):
    """Check if the RDMRecordConverter can actually update record data."""
    converter = RDMRecordConverter()
    record = example_data["records"][0]
    record_data = record.model.data.copy()

    identity = Identity(1)
    identity.provides.add(any_user)
    fake_date = "1969-06-09"
    patch_data = {
        "access": {
            "access_right": "closed",
            "files_restricted": True,
            "metadata_restricted": False,
        },
        "metadata": {
            "publication_date": fake_date,
        },
    }

    new_record = converter.update_record(record, patch_data, identity)
    new_data = new_record.model.data
    assert new_data != record_data
    assert new_data["access"]["access_right"] == "closed"
    assert new_data["access"]["files_restricted"]
    assert not new_data["access"]["metadata_restricted"]
    assert new_data["metadata"]["publication_date"] == fake_date


def test_get_dataset_metadata_model(app, example_data):
    record = example_data["records"][0]
    converter = RDMRecordConverter()

    metadata = converter.get_dataset_metadata_model(record)
    assert metadata.get("description")
    assert metadata.get("language")
    assert metadata.get("metadata_standard_id", {}).get("identifier")
    assert metadata.get("metadata_standard_id", {}).get("type")


def test_convert_record(app):
    # TODO prepare an example maDMP for verifying convert_record(), once Invenio's
    #      metadata model has been fixed
    pass


def test_convert_dataset(app):
    # TODO prepare an example record for verifying convert_dataset(), once Invenio's
    #      metadata model has been fixed
    pass
