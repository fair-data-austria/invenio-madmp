"""Helper functions for Invenio-maDMP."""

import re
import uuid
from datetime import datetime
from typing import Dict

from flask import current_app as app
from invenio_accounts.models import User
from invenio_pidstore.models import PersistentIdentifier as PID
from invenio_rdm_records.marshmallow import MetadataSchemaV1
from invenio_rdm_records.models import BibliographicRecordDraft
from invenio_rdm_records.pid_manager import BibliographicPIDManager
from invenio_records.models import RecordMetadata
from invenio_records_resources.services import MarshmallowDataValidator
from werkzeug.utils import import_string

from .licenses import License

default_data_validator = MarshmallowDataValidator(schema=MetadataSchemaV1)
default_pid_manager = BibliographicPIDManager()

url_identifier_pattern = re.compile(r"https?://.*?/(.*)")
name_pattern_1 = re.compile(r"([^\s]+)\s+([^\s]+)")
name_pattern_2 = re.compile(r"([^\s]+),\s+([^\s]+)")


def is_identifier_type_allowed(id_type: str, contributor_dict: Dict = None):
    """Check if the identifier type is allowed for contributors."""
    return id_type in ["Orcid", "ror"]


def parse_date(date_str):
    """Parse the given date string."""
    return datetime.fromisoformat(date_str)


def format_date(date):
    """Format the given date."""
    return date.isoformat()


def distribution_matches_us(distribution_dict):
    """Check if the 'host' of the distribution matches our repository."""
    host = distribution_dict.get("host", {})
    url_matches = host.get("url", None) == app.config["MADMP_HOST_URL"]
    title_matches = host.get("title", None) == app.config["MADMP_HOST_TITLE"]
    return url_matches or title_matches


def translate_dataset_type(dataset_dict):
    """Map the maDMP dataset type using the configured dictionaries."""
    type_ = dataset_dict.get("type", None)
    trans_d = app.config["MADMP_RESOURCE_TYPE_TRANSLATION_DICT"] or {}
    sub_trans_d = app.config["MADMP_RESOURCE_SUBTYPE_TRANSLATION_DICT"] or {}

    resource_type = {
        "type": trans_d.get(type_, "other"),  # TODO check vocabulary
        "subtype": sub_trans_d.get(type_, ""),  # TODO check vocab
    }

    return resource_type


def translate_license(license_dict):
    """Try to find the referenced license in the list of known licenses."""
    licenses = app.config["MADMP_LICENSES"]

    matching_licenses = [
        lic for lic in licenses if lic.matches(*license_dict.values())
    ]

    if matching_licenses:
        lic = matching_licenses[0]
    else:
        lic = License("Other", "Other", "", "Other")

    return lic.to_dict()


def translate_person_details(person_dict: Dict) -> Dict:
    """Try to find out additional information for a person.

    Tries to separate the person's full name into a given and family name by
    applying simple patterns.
    :param person_dict: [description]
    :type person_dict: dict
    :return: A dictionary with additional information about the person.
    :rtype: dict
    """
    additional_infos = {}
    name = person_dict.get("name", None)

    if name:
        m1 = name_pattern_1.match(name)
        m2 = name_pattern_2.match(name)
        if m1:
            additional_infos["given_name"] = m1.group(1)
            additional_infos["family_name"] = m1.group(2)
        elif m2:
            additional_infos["given_name"] = m2.group(2)
            additional_infos["family_name"] = m2.group(1)

    return additional_infos


def create_new_record(
    record_dict,
    record_api_class=BibliographicRecordDraft,
    data_validator=default_data_validator,
    pid_manager=default_pid_manager,
):
    """Create a new record (draft) with the given metadata in record_dict.

    :param record_dict: Dictionary with metadata to use for the new record
    :type record_dict: dict
    :param data_validator: The Marshmallow data validator to use
    :param pid_manager: The PID manager to use
    :return: The created record (draft)
    """
    # TODO check if the following is correct (and necessary):
    # identity = Identity(1)
    # identity.provides.add(any_user)
    # require_permission(identity, "create")
    data = data_validator.validate(record_dict, partial=True)
    rec_uuid = uuid.uuid4()
    pid_manager.mint(record_uuid=rec_uuid, data=data)
    draft = record_api_class.create(data, id_=rec_uuid)

    return draft


def fetch_unassigned_record(dataset_identifier, distribution_access_url=None):
    """Try to find a (yet unassigned) record via the specified identifiers.

    Try to find a record with an associated PID that has the same value as the
    specified dataset identifier.
    If the distribution's (i.e. record's) access URL is specified, it will
    take precedence over the dataset's identifier for the search.
    :param dataset_identifier: The dataset's identifier
    :type dataset_identifier: str
    :param distribution_access_url: The URL endpoint for the Record
    :type distribution_access_url: str
    :return: The Record identified by the provided means
    :rtype: Record
    """
    rec = None

    if distribution_access_url:
        # TODO use a better variant of getting the record via the access url
        #      (=landing page)
        p = r"https?://.*?/records/(.*)"
        match = re.match(p, distribution_access_url)
        if match:
            recid = match.group(1)
            pid = PID.get("recid", recid)
            if pid is not None:
                rec = RecordMetadata.query.get(
                    pid.object_uuid
                )  # TODO may also be a Draft?
                if rec:
                    return rec

    # in case of a DOI, remove the possibly leading "https://doi.org/"
    dataset_identifier = strip_identifier(dataset_identifier)

    pid = PID.query.filter(PID.pid_value == dataset_identifier).one_or_none()
    if pid is not None:
        rec = RecordMetadata.query.get(pid.object_uuid)  # TODO may be a Draft?

    return rec


def find_user(email):
    """Find a user by their e-mail address."""
    user = User.query.filter(User.email == email).one_or_none()
    return user


def strip_identifier(identifier):
    """Strip the URL prefix from PIDs (e.g.: https://doi.org/...)."""
    match = url_identifier_pattern.match(identifier)
    if match:
        return match.group(1)

    return identifier


def get_or_import(value, default=None):
    """Try an import if value is an endpoint string, or return value itself."""
    if isinstance(value, str):
        return import_string(value)
    elif value:
        return value

    return default
