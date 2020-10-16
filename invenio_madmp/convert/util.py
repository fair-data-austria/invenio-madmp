"""TODO."""


from typing import List

from flask import current_app as app
from flask_principal import Identity
from invenio_access.permissions import any_user
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier as PID

from ..models import DataManagementPlan as DMP
from ..models import Dataset
from ..util import (
    distribution_matches_us,
    fetch_unassigned_record,
    is_identifier_type_allowed,
    translate_person_details,
)


def is_relevant_contributor(role: str) -> bool:
    """Check if the contributor is relevant as owner, based on their role."""
    if not app.config["MADMP_RELEVANT_CONTRIBUTOR_ROLES"]:
        return True

    return role in app.config["MADMP_RELEVANT_CONTRIBUTOR_ROLES"]


def filter_contributors(contrib_dict_list: List[dict]) -> List[dict]:
    """Filter the list of contributors by their roles."""
    return [
        contrib
        for contrib in contrib_dict_list
        if is_relevant_contributor(contrib["role"])
    ]


def map_contact(contact_dict):
    """Get the contact person's e-mail address."""
    return contact_dict.get("mbox", app.config["MADMP_DEFAULT_CONTACT"])


def map_creator(creator_dict):
    """Map the DMP's creator(s) to the record's creator(s)."""
    # TODO creator = uploader?
    cid = creator_dict["contributor_id"]
    identifiers = (
        {cid["type"]: cid["identifier"]}
        if is_identifier_type_allowed(cid["type"], creator_dict)
        else {}
    )

    affiliations = []

    creator = {
        "name": creator_dict["name"],
        "type": "Personal",  # TODO ?
        "given_name": None,
        "family_name": None,
        "identifiers": identifiers,
        "affiliations": affiliations,
    }

    additional_details = {
        k: v
        for k, v in translate_person_details(creator_dict).items()
        if k in creator.keys() and v is not None
    }
    creator.update(additional_details)

    return {k: v for k, v in creator.items() if v is not None}


def map_contributor(contributor_dict, role_idx=0):
    """Map the DMP's contributor(s) to the record's contributor(s)."""
    cid = contributor_dict["contributor_id"]
    identifiers = (
        {cid["type"]: cid["identifier"]}
        if is_identifier_type_allowed(cid["type"], contributor_dict)
        else {}
    )

    affiliations = []

    # note: currently (sept 2020), the role is a SanitizedUnicode in the
    #       rdm-records marshmallow schema
    contributor = {
        "name": contributor_dict["name"],
        "type": "Personal",  # TODO ?
        "given_name": None,
        "family_name": None,
        "identifiers": identifiers,
        "affiliations": affiliations,
        "role": contributor_dict["role"][role_idx],
    }

    additional_details = {
        k: v
        for k, v in translate_person_details(contributor_dict).items()
        if k in contributor.keys() and v is not None
    }
    contributor.update(additional_details)

    return {k: v for k, v in contributor.items() if v is not None}


def matching_distributions(dataset_dict):
    """Fetch all matching distributions from the dataset."""
    return [
        dist
        for dist in dataset_dict.get("distribution", [])
        if distribution_matches_us(dist)
    ]


def convert_dmp(
    madmp_dict: dict, hard_sync: bool = False, identity: Identity = None
) -> List:
    """Map the maDMP's dictionary to a number of Invenio RDM Records."""
    with db.session.no_autoflush:
        # disabling autoflush, because we don't want to flush unfinished parts
        # (this caused issues when Dataset.record_pid_id was not nullable)
        identity = identity or any_user
        contrib_list = madmp_dict.get("contributor", [])
        contact = map_contact(madmp_dict.get("contact", {}))
        contribs = list(map(map_contributor, contrib_list))
        creators = list(map(map_creator, contrib_list))
        dmp_id = madmp_dict.get("dmp_id", {}).get("identifier")

        found_dmp = DMP.get_by_dmp_id(dmp_id)
        dmp = found_dmp or DMP(dmp_id=dmp_id)
        old_datasets = dmp.datasets.copy()

        for dataset in madmp_dict.get("dataset", []):
            distribs = matching_distributions(dataset)
            if not distribs:
                # our repository is not listed as host for any
                # of the distributions

                if not dataset.get("distribution"):
                    # the dataset doesn't have any distributions specified...
                    # weird.
                    # TODO how do we want to handle this case?
                    #      do we want to create the first distribution?
                    pass

                else:
                    # there are distributions, but just not in our repo: ignore
                    pass

            else:
                # we're not interested in datasets without deposit in Invenio
                # TODO: to be unique, we need the dataset_id identifier and
                #       type, which translate to pid_value and pid_type
                #       (the latter might require some mapping) -- then,
                #       PID provides a method PID.get(pid_type, pid_value)
                dataset_id = dataset.get("dataset_id", {}).get("identifier")

                if len(distribs) > 1:
                    if not app.config["MADMP_ALLOW_MULTIPLE_DISTRIBUTIONS"]:
                        raise Exception(
                            (
                                "dataset (%s) has multiple (%s) matching "
                                "distributions on this host, "
                                "but only one is allowed"
                            )
                            % (dataset_id, len(distribs))
                        )

                records_and_converters = []
                for distrib in distribs:
                    # iterate over all dataset[].distribution[] elements that
                    # match our repository, and create a record for each
                    # distribution
                    # note: we assume at most one distribution per host, as
                    #       the same distribution with several formats can be
                    #       published in a single ZIP file (i.e. as a single
                    #       record)

                    converter = get_matching_converter(distrib, dataset, madmp_dict)

                    if converter is None:
                        raise LookupError(
                            "no matching converter registered for dataset: %s" % dataset
                        )

                    record_data = converter.convert_dataset(
                        distrib,
                        dataset,
                        madmp_dict,
                        creators=creators,
                        contributors=contribs,
                        contact=contact,
                    )

                    records_and_converters.append((record_data, converter))

                found_ds = Dataset.get_by_dataset_id(dataset_id)
                ds = found_ds or Dataset(dataset_id=dataset_id)
                if found_ds is not None and found_ds in old_datasets:
                    old_datasets.remove(found_ds)

                if ds.dataset_id not in [ds.dataset_id for ds in dmp.datasets]:
                    dmp.datasets.append(ds)

                if ds.record is None:
                    record = fetch_unassigned_record(
                        dataset_id, distribs[0].get("access_url")
                    )
                    if record is not None:
                        # TODO find better way of getting the "best" identifier
                        #      (e.g. first check for DOI, then whatever, and as
                        #       fallback the Recid)
                        #      note: the best would of course be the one
                        #            matching the dataset_id!
                        ds.record_pid = PID.query.filter(
                            PID.object_uuid == record.id
                        ).first()
                    else:
                        # create a new Draft
                        # TODO make the logic for deciding which record to
                        #      create more flexible
                        record_data, converter = records_and_converters[0]
                        identity = Identity(1)  # TODO find out ID of owner?
                        identity.provides.add(any_user)
                        rec = converter.create_record(record_data, identity)
                        ds.record_pid = rec.pid

                elif hard_sync:
                    # hard-sync the dataset's associated record
                    record_data, converter = records_and_converters[0]
                    identity = Identity(1)  # TODO find out ID of owner?
                    converter.update_record(ds.record, record_data, identity)

        for old_ds in old_datasets:
            # unlink the datasets that were previously connected to the DMP,
            # but are no longer mentioned in the maDMP JSON
            # note: if the DMP is new, old_datasets is necessarily empty
            dmp.datasets.remove(old_ds)

        # TODO commit DB session & index created drafts
        return dmp


from .records.base import BaseRecordConverter  # noqa - fixes circular import issue


def get_matching_converter(
    distribution_dict: dict, dataset_dict: dict, dmp_dict: dict
) -> BaseRecordConverter:
    """TODO."""
    for converter in app.config["MADMP_RECORD_CONVERTERS"]:
        if converter.matches(distribution_dict, dataset_dict, dmp_dict):
            return converter

    return app.config["MADMP_FALLBACK_RECORD_CONVERTER"]
