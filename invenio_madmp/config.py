# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for maDMP integration."""

from typing import Dict, List

from .convert.records.base import BaseRecordConverter
from .convert.records.rdm_records import RDMRecordConverter
from .licenses import KNOWN_LICENSES

# for finding matching distributions
MADMP_HOST_URL = "https://data.tuwien.ac.at"
MADMP_HOST_TITLE = "TU Data"

# the expected token (shared secret) in the REST endpoints
# 'None' means that the check for authorization is disabled
MADMP_COMMUNICATION_TOKEN = "CHANGE ME"

# default mapping values
MADMP_DEFAULT_LANGUAGE = "eng"
MADMP_DEFAULT_CONTACT = "info@invenio.org"
MADMP_DEFAULT_DATA_ACCESS = "open"

# the ID of the user to be set as record creator
# 'None' lets the RecordConverter decide
# TODO change this: instead, combine with MADMP_COMMUNICATION_TOKEN
#                   on successful auth, set the current_user property according to this
#                   user right here, and use them as creator in convert_dmp
#                   (if current_user is not set, parse the creator from the DMP)
MADMP_RECORD_CREATOR_USER_ID = None

# record converters
MADMP_RECORD_CONVERTERS: List[BaseRecordConverter] = []
MADMP_FALLBACK_RECORD_CONVERTER: BaseRecordConverter = RDMRecordConverter()

# list of contributor roles that are considered to be record owners
# an empty list makes all contributors to record owners, regardless of their roles
MADMP_RELEVANT_CONTRIBUTOR_ROLES = []

# determine of some semantic errors should be ignored
MADMP_ALLOW_MULTIPLE_DISTRIBUTIONS = False
MADMP_ALLOW_UNKNOWN_CONTRIBUTORS = False

# dictionaries for mapping resource (sub-) types
MADMP_RESOURCE_TYPE_TRANSLATION_DICT: Dict[str, str] = {}
MADMP_RESOURCE_SUBTYPE_TRANSLATION_DICT: Dict[str, str] = {}

# list of known licenses (as License objects)
MADMP_LICENSES = KNOWN_LICENSES
