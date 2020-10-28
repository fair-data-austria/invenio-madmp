# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests for conversion utilities."""

from datetime import datetime

import pytest
from invenio_accounts.models import User

from invenio_madmp.ext import InvenioMaDMP
from invenio_madmp.util import (
    fetch_unassigned_record,
    find_user,
    get_or_import,
    parse_date,
    translate_person_details,
)

# -------------------->
# find user per email
# -------------------->


def test_find_by_email(all_required_accounts):
    """Check if users can be found by their email address."""
    all_users = User.query.all()
    assert len(all_users) > 0

    for u in all_users:
        v = find_user(u.email)
        assert u == v


# ------------------------>
# person name translation
# ------------------------>


def test_name_translation():
    """Check if the heuristic for splitting the full into given/family name works."""
    expected = {"given_name": "Maximilian", "family_name": "Moser"}
    style1, style2 = {"name": "Maximilian Moser"}, {"name": "Moser, Maximilian"}

    res1 = translate_person_details(style1)
    res2 = translate_person_details(style2)

    assert res1 == expected
    assert res2 == expected


# ----------->
# parse_date
# ----------->


def test_parse_iso_date():
    date = datetime.now()
    fmt_date = date.isoformat()

    parsed_date = parse_date(fmt_date, silent=False)
    assert parsed_date == date


def test_parse_invalid_date():
    with pytest.raises(ValueError):
        fmt_date = "Hello!"
        parse_date(fmt_date, silent=False)


def test_parse_invalid_date_silently():
    fmt_date = "Hello!"
    parsed_date = parse_date(fmt_date, silent=True)
    assert parsed_date is None


# -------------->
# get_or_import
# -------------->
#
# check if the 'get_or_import' utility does what it is supposed to do
# as it is a relatively fundamental helper
#


def test_get_or_import_object():
    def greet():
        print("Hello!")

    obj = get_or_import(greet, None)
    assert obj is greet


def test_get_or_import_string():
    obj = get_or_import("invenio_madmp.ext:InvenioMaDMP", None)
    assert obj is InvenioMaDMP


def test_get_or_import_invalid_string():
    with pytest.raises(ImportError):
        get_or_import("invenio_madmp.invalid_module:greet", lambda: print("Hello!"))


def test_get_or_import_fallback():
    fallback = object()
    result = get_or_import(None, fallback)
    assert result is fallback


# ------------------------>
# fetch unassigned record
# ------------------------>


def test_fetch_unassigned_record_via_url(example_data):
    records = example_data["records"]
    record = records[0]
    access_url = "https://data.tuwien.ac.at/records/%s" % record.pid.pid_value
    fetched = fetch_unassigned_record("some-identifier", access_url)
    assert fetched == record


def test_fetch_unassigned_record_via_dataset_id(example_data):
    records = example_data["records"]
    record = records[0]
    fetched = fetch_unassigned_record(record.pid.pid_value, None)
    assert fetched == record


def test_fetch_unassigned_record_nonexisting(example_data):
    made_up_id, made_up_url = "non-existing", "https://data.tuwien.ac.at/records/na"
    fetched = fetch_unassigned_record(made_up_id, made_up_url)
    assert fetched is None
