# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests for high-level conversion functions."""

import pytest
from invenio_accounts.models import User

from invenio_madmp.convert import convert_dmp


def test_successful_conversion(
    app, example_madmps_for_invenio, all_required_accounts
):
    for _, madmp in example_madmps_for_invenio.items():
        dmp = convert_dmp(madmp["dmp"])

        assert dmp is not None
        assert dmp.dmp_id == madmp["dmp"]["dmp_id"]["identifier"]


def test_no_users(app, example_madmps_for_invenio_requiring_users):
    assert len(User.query.all()) == 0

    problematic_madmps = example_madmps_for_invenio_requiring_users
    for madmp in problematic_madmps:
        with pytest.raises(LookupError):
            madmp = problematic_madmps[madmp]["dmp"]
            convert_dmp(madmp)
