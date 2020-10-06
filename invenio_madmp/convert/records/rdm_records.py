"""Record Converter for RDM Records."""
# TODO: make the functions used for mapping RDA Common Standard to
#       Invenio metadata model configurable
#       (because invenio doesn't necessarily use the current
#        Invenio-RDM-Records metadata model)

from datetime import datetime

from flask import current_app as app
from flask_principal import Identity
from invenio_access.permissions import any_user
from invenio_rdm_records.permissions import RDMRecordPermissionPolicy
from invenio_rdm_records.services import BibliographicRecordService, \
    BibliographicRecordServiceConfig
from invenio_records.api import Record
from invenio_records_permissions.generators import AnyUser

from ...util import find_user, format_date, parse_date, \
    translate_dataset_type, translate_license
from ..util import map_contact, map_contributor, map_creator
from .base import BaseRecordConverter


class PermissionPolicy(RDMRecordPermissionPolicy):
    """TODO delet this (https://tinyurl.com/y69derx3)."""

    can_update = [AnyUser()]


class ServiceConfig(BibliographicRecordServiceConfig):
    """TODO delet this (https://tinyurl.com/y69derx3)."""

    permission_policy_cls = PermissionPolicy


class RDMRecordConverter(BaseRecordConverter):
    """TODO."""

    def __init__(self):
        """TODO."""
        self.record_service = BibliographicRecordService(config=ServiceConfig)

    def map_access_right(self, distribution_dict):
        """Get the 'access_right' from the distribution."""
        return distribution_dict.get(
            "data_access", app.config["MADMP_DEFAULT_DATA_ACCESS"]
        )

    def map_resource_type(self, dataset_dict):
        """Map the resource type of the dataset."""
        return translate_dataset_type(dataset_dict)

    def map_title(self, dataset_dict):
        """Map the dataset's title to the record's title."""
        return {
            "title": dataset_dict.get("title", "[No Title]"),
            "type": "MainTitle",  # TODO check vocabulary
            "lang": dataset_dict.get(
                "language", app.config["MADMP_DEFAULT_LANGUAGE"]
            ),
        }

    def map_language(self, dataset_dict):
        """Map the dataset's language to the record's language."""
        # note: both RDA-CS and Invenio-RDM-Records use ISO 639-3
        return dataset_dict.get(
            "language", app.config["MADMP_DEFAULT_LANGUAGE"]
        )

    def map_license(self, license_dict):
        """Map the distribution's license to the record's license."""
        return translate_license(license_dict)

    def map_description(self, dataset_dict):
        """Map the dataset's description to the record's description."""
        # possible description types, from the rdm-records marshmallow schema:
        #
        # "Abstract", "Methods", "SeriesInformation", "TableOfContents",
        # "TechnicalInfo", "Other"

        return {
            "description": dataset_dict.get("description", "[No Description]"),
            "type": "Other",
            "lang": dataset_dict.get(
                "language", app.config["MADMP_DEFAULT_LANGUAGE"]
            ),
        }

    def convert_dataset(
        self,
        distribution_dict,
        dataset_dict,
        dmp_dict,
        contact=None,
        creators=None,
        contributors=None,
    ):
        """Map the dataset distribution to metadata for a record in Invenio."""
        contact_dict = dmp_dict.get("contact", {})
        contributor_list = dmp_dict.get("contributor", [])

        if contact is None:
            contact = map_contact(contact_dict)

        if contributors is None:
            contributors = list(map(map_contributor, contributor_list))

        if creators is None:
            creators = list(map(map_creator, contributor_list))

        resource_type = self.map_resource_type(dataset_dict)
        access_right = self.map_access_right(distribution_dict)
        titles = [self.map_title(dataset_dict)]
        language = self.map_language(dataset_dict)
        licenses = list(
            map(self.map_license, distribution_dict.get("license", []))
        )
        descriptions = [self.map_description(dataset_dict)]
        dates = []

        min_lic_start = None
        for lic in distribution_dict.get("license"):
            lic_start = parse_date(lic["start_date"])

            if min_lic_start is None or lic_start < min_lic_start:
                min_lic_start = lic_start

        record = {
            "access_right": access_right,
            "contact": contact,
            "resource_type": resource_type,
            "creators": creators,
            "titles": titles,
            "contributors": contributors,
            "dates": dates,
            "language": language,
            "licenses": licenses,
            "descriptions": descriptions,
            "publication_date": datetime.utcnow().isoformat(),
        }

        if min_lic_start is None or datetime.utcnow() < min_lic_start:

            # the earliest license start date is in the future:
            # that means there's an embargo
            fmt_date = format_date(min_lic_start, "%Y-%m-%d")
            record["embargo_date"] = fmt_date

        files_restricted = access_right != "open"
        metadata_restricted = False
        record["_access"] = {
            "files_restricted": files_restricted,
            "metadata_restricted": metadata_restricted,
        }

        # TODO find owners by contributors and contact fields from DMP
        emails = [creator.get("mbox") for creator in contributor_list]
        users = [
            user
            for user in (
                find_user(email) for email in emails if email is not None
            )
        ]

        allow_unknown_contribs = app.config["MADMP_ALLOW_UNKNOWN_CONTRIBUTORS"]
        if None in users and not allow_unknown_contribs:
            unknown = [email for email in emails if find_user(email) is None]
            raise LookupError(
                "DMP contains unknown contributors: %s" % unknown
            )

        users = [user for user in users if user is not None]

        if not users:
            raise LookupError(
                "no registered users found for any email address: %s" % emails
            )

        record["_owners"] = {u.id for u in users}
        record["_created_by"] = users[
            0
        ].id  # TODO fallback user? some admin? or exception?

        return record

    def create_record(self, record_data: dict, identity: Identity) -> Record:
        """TODO."""
        # note: the BibliographicRecordService will return an IdentifiedRecord,
        #       which wraps the record/draft and its PID into one object
        # note: Service.create() will already commit the changes to DB!
        draft = self.record_service.create(identity, record_data)
        return draft.record

    def update_record(
        self,
        original_record: Record,
        new_record_data: dict,
        identity: Identity,
    ):
        """TODO."""
        new_data = new_record_data.copy()
        del new_data["_owners"]
        del new_data["_creator"]

        identity.provides.add(any_user)
        if self.is_draft(original_record):
            self.record_service.update_draft(
                identity, original_record["recid"], new_data
            )

        elif self.is_record(original_record):
            self.record_service.update(
                identity, original_record["recid"], new_data
            )
