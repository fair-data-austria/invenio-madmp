"""Record Converter for RDM Records."""

from datetime import datetime
from typing import Optional

from flask import current_app as app
from flask_principal import Identity
from invenio_access.permissions import any_user
from invenio_jsonschemas import current_jsonschemas
from invenio_rdm_records.models import BibliographicRecord, BibliographicRecordDraft
from invenio_rdm_records.permissions import RDMRecordPermissionPolicy
from invenio_rdm_records.services import (
    BibliographicRecordService,
    BibliographicRecordServiceConfig,
)
from invenio_records.api import Record
from invenio_records_permissions.generators import AnyUser

from ...util import (
    find_user,
    format_date,
    parse_date,
    translate_dataset_type,
    translate_license,
)
from ..util import filter_contributors, map_contact, map_contributor, map_creator
from .base import BaseRecordConverter


class PermissionPolicy(RDMRecordPermissionPolicy):
    """TODO delet this (https://tinyurl.com/y69derx3)."""

    can_update = [AnyUser()]


class ServiceConfig(BibliographicRecordServiceConfig):
    """TODO delet this (https://tinyurl.com/y69derx3)."""

    permission_policy_cls = PermissionPolicy


class RDMRecordConverter(BaseRecordConverter):
    """RecordConverter using the Invenio-RDM-Records metadata model."""

    def __init__(self):
        """Initialize a new RDMRecordConverter."""
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
        """Map the dataset's title to the Record's title."""
        return {
            "title": dataset_dict.get("title", "[No Title]"),
            "type": "MainTitle",  # TODO check vocabulary
            "lang": dataset_dict.get("language", app.config["MADMP_DEFAULT_LANGUAGE"]),
        }

    def map_language(self, dataset_dict):
        """Map the dataset's language to the Record's language."""
        # note: both RDA-CS and Invenio-RDM-Records use ISO 639-3
        return dataset_dict.get("language", app.config["MADMP_DEFAULT_LANGUAGE"])

    def map_license(self, license_dict):
        """Map the distribution's license to the Record's license."""
        return translate_license(license_dict)

    def map_description(self, dataset_dict):
        """Map the dataset's description to the Record's description."""
        # possible description types, from the rdm-records marshmallow schema:
        #
        # "Abstract", "Methods", "SeriesInformation", "TableOfContents",
        # "TechnicalInfo", "Other"

        return {
            "description": dataset_dict.get("description", "[No Description]"),
            "type": "Other",
            "lang": dataset_dict.get("language", app.config["MADMP_DEFAULT_LANGUAGE"]),
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
        """Map the dataset distribution to metadata for a Record in Invenio."""
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
        licenses = list(map(self.map_license, distribution_dict.get("license", [])))
        descriptions = [self.map_description(dataset_dict)]
        dates = []

        min_lic_start = None
        for lic in distribution_dict.get("license"):
            lic_start = parse_date(lic["start_date"])

            if min_lic_start is None or lic_start < min_lic_start:
                min_lic_start = lic_start

        record = {
            "access": {
                "access_right": access_right,
            },
            "metadata": {
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
            },
        }

        if min_lic_start is None or datetime.utcnow() < min_lic_start:
            # the earliest license start date is in the future:
            # that means there's an embargo
            fmt_date = format_date(min_lic_start, "%Y-%m-%d")
            record["metadata"]["embargo_date"] = fmt_date

        files_restricted = access_right != "open"
        metadata_restricted = False
        record["access"].update(
            {
                "files_restricted": files_restricted,
                "metadata_restricted": metadata_restricted,
            }
        )

        # parse the record owners from the contributors (based on their roles)
        filtered_contribs = filter_contributors(contributor_list)
        if not filtered_contribs:
            message = "the contributors contain no suitable record owners by role"
            raise ValueError(message)

        emails = [creator.get("mbox") for creator in filtered_contribs]
        users = [
            user for user in (find_user(email) for email in emails if email is not None)
        ]

        allow_unknown_contribs = app.config["MADMP_ALLOW_UNKNOWN_CONTRIBUTORS"]
        if None in users and not allow_unknown_contribs:
            # if there are relevant owners who are unknown to us
            unknown = [email for email in emails if find_user(email) is None]
            raise LookupError("DMP contains unknown contributors: %s" % unknown)

        users = [user for user in users if user is not None]
        if not users:
            raise LookupError(
                "no registered users found for any email address: %s" % emails
            )

        creator_id = app.config["MADMP_RECORD_CREATOR_USER_ID"] or users[0].id
        record["access"]["owners"] = {u.id for u in users}
        record["access"]["created_by"] = creator_id

        return record

    def create_record(self, record_data: dict, identity: Identity) -> Record:
        """Create a new Draft from the specified metadata."""
        # note: the BibliographicRecordService will return an IdentifiedRecord,
        #       which wraps the record/draft and its PID into one object
        # note: Service.create() will already commit the changes to DB!
        draft = self.record_service.create(identity, record_data)
        return draft._record

    def update_record(
        self,
        original_record: Record,
        new_record_data: dict,
        identity: Identity,
    ):
        """Update the metadata of the specified Record with the new data."""
        identity.provides.add(any_user)

        # because partial updates are currently not working, we use the data from the
        # original record and update the metadata dictionary
        data = original_record.model.data.copy()
        new_data = new_record_data.copy()

        if "access" in new_data:
            if "owners" in new_data["access"]:
                del new_data["access"]["owners"]
            if "created_by" in new_data["access"]:
                del new_data["access"]["created_by"]

            data["access"].update(new_data["access"])

        if "metadata" in new_data:
            data["metadata"].update(new_data["metadata"])

        if self.is_draft(original_record):
            result = self.record_service.update_draft(
                identity=identity,
                id_=original_record["id"],
                data=data,
            )

        elif self.is_record(original_record):
            result = self.record_service.update(
                identity=identity,
                id_=original_record["id"],
                data=data,
            )

        if result is not None:
            return result._record

    def convert_record(self, record: Record) -> dict:
        """Convert the Record into a maDMP dataset distribution dictionary."""
        metadata = record["metadata"]

        # we prefer the english titles, if there are any
        # the 'empty' list is there to avoid errors with the indexing operator later on
        all_descrs = metadata["descriptions"]
        english_descrs = [t for t in all_descrs if t["lang"] == "eng"]
        all_titles = metadata["titles"]
        english_titles = [t for t in all_titles if t["lang"] == "eng"]
        empty = [{"title": None, "description": None}]

        publication_date = parse_date(metadata["publication_date"])
        embargo_date = parse_date(metadata["embargo_date"])
        license_start_date = embargo_date or publication_date or datetime.now().date()

        licenses = [
            {"license_ref": lic["uri"], "start_date": format_date(license_start_date)}
            for lic in metadata["licenses"]
        ]

        distribution = {
            "access_url": None,  # TODO
            "download_url": None,  # TODO
            "title": (english_titles + all_titles + empty)[0]["title"],
            "description": (english_descrs + all_descrs + empty)[0]["description"],
            "byte_size": None,  # TODO
            "data_access": record["access"]["access_right"],
            "license": licenses,
            "personal_data": None,  # TODO
            "sensitive_data": None,  # TODO
            "format": metadata["resource_type"]["type"],  # TODO
            "available_until": None,  # TODO
        }

        # filter out the values that haven't been supplied
        distribution = {k: v for k, v in distribution.items() if v is not None}
        if not distribution["license"]:
            del distribution["license"]

        return distribution

    def get_dataset_metadata_model(self, record: Record = None) -> Optional[dict]:
        """Get the RDA DMP metadata property used by the Record or this Converter."""
        schema = record.get("$schema") or "records/record-v1.0.0.json"
        metadata_url = current_jsonschemas.path_to_url(schema)

        if metadata_url is not None:
            return {
                "description": "Datacite-based metadata model for Invenio-RDM-Records",
                "language": "eng",
                "metadata_standard_id": {
                    "identifier": metadata_url,
                    "type": "url",
                },
            }

        return None

    def is_draft(self, record: Record) -> bool:
        """Check if the specified object is a suitable Record."""
        return isinstance(record, BibliographicRecordDraft)

    def is_record(self, record: Record) -> bool:
        """Check if the specified object is a suitable Draft."""
        return isinstance(record, BibliographicRecord)

    def matches_dataset(self, dataset_dict: dict, dmp_dict: dict = None) -> bool:
        """Check if this converter is suitable for the specified maDMP dataset."""
        for metadata in dataset_dict.get("metadata", []):
            standard_id = metadata.get("metadata_standard_id", {})
            identifier = standard_id.get("identifier")
            if "schema.datacite.org" in identifier:
                return True

        return False

    def matches_record(self, record: Record) -> bool:
        """Check if this converter is suitable for the specified Record."""
        return self.is_draft(record) or self.is_record(record)
