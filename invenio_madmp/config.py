# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for maDMP integration."""

from .convert.records.rdm_records import RDMRecordConverter
from .licenses import KNOWN_LICENSES

MADMP_HOST_URL = "https://data.tuwien.ac.at"
MADMP_HOST_TITLE = "TU Data"

MADMP_DEFAULT_LANGUAGE = "eng"
MADMP_DEFAULT_CONTACT = "info@invenio.org"
MADMP_DEFAULT_DATA_ACCESS = "open"

MADMP_RECORD_CONVERTERS = []
MADMP_FALLBACK_RECORD_CONVERTER = RDMRecordConverter()

MADMP_ALLOW_MULTIPLE_DISTRIBUTIONS = False

MADMP_RESOURCE_TYPE_TRANSLATION_DICT = {}
MADMP_RESOURCE_SUBTYPE_TRANSLATION_DICT = {}

MADMP_LICENSES = KNOWN_LICENSES
