# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for maDMP integration."""

from typing import Dict, List

import invenio_records.signals as rec_signals

from . import signals as dmp_signals
from .comm import observers as handlers
from .convert.records.base import BaseRecordConverter
from .convert.records.rdm_records import RDMRecordConverter
from .licenses import KNOWN_LICENSES

# information regarding dataset distributions' hosts
# (host url and title are also used for finding matching distributions)
MADMP_HOST_URL = "https://invenio.cern.ch"
MADMP_HOST_TITLE = "Invenio RDM"
MADMP_HOST_DESCRIPTION = "RDM Repository hosted by CERN"
MADMP_HOST_AVAILABILITY = "99.5"
MADMP_HOST_BACKUP_FREQUENCY = "weekly"
MADMP_HOST_BACKUP_TYPE = "tapes"
MADMP_HOST_CERTIFIED_WITH = "coretrustseal"
MADMP_HOST_GEO_LOCATION = "CH"
MADMP_HOST_SUPP_VERSIONING = "yes"
MADMP_HOST_STORAGE_TYPE = "disks"
MADMP_HOST_PID_SYSTEM = ["other"]

# the expected token (shared secret) in the REST endpoints
# 'None' means that the check for authorization is disabled
MADMP_COMMUNICATION_TOKEN = "CHANGE ME"

# default mapping values
MADMP_DEFAULT_LANGUAGE = "eng"
MADMP_DEFAULT_CONTACT = "info@invenio.org"
MADMP_DEFAULT_DATA_ACCESS = "open"

# record converters
MADMP_RECORD_CONVERTERS: List[BaseRecordConverter] = []
MADMP_FALLBACK_RECORD_CONVERTER: BaseRecordConverter = RDMRecordConverter

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

# endpoint URLs for the other side of the integration
MADMP_DMP_TOOL_DMP_ENDPOINT_URL: str = "https://localhost:3000/dmps/%s"
MADMP_DMP_TOOL_DMPS_ENDPOINT_URL: str = "https://localhost:3000/dmps"
MADMP_DMP_TOOL_DATASET_ENDPOINT_URL: str = "https://localhost:3000/datasets/%s"
MADMP_DMP_TOOL_DATASETS_ENDPOINT_URL: str = "https://localhost:3000/datasets"

# list of pairs (signal, handler), where each handler should be connected
# (i.e. registered as handler) to the corresponding signal
MADMP_SIGNAL_HANDLERS: List = [
    (dmp_signals.dmp_dataset_added, handlers.prepare_sending_new_dataset),
    (dmp_signals.dataset_deleted, handlers.prepare_sending_deleted_dataset),
    (rec_signals.after_record_delete, handlers.prepare_sending_distribution_deletion),
    (dmp_signals.dataset_record_pid_changed, handlers.prepare_sending_changed_dataset),
    (rec_signals.after_record_update, handlers.prepare_sending_distribution_update),
]
