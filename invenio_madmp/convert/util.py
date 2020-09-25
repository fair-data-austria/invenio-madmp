"""TODO."""


from typing import List

from flask import current_app as app
from invenio_pidstore.models import PersistentIdentifier as PID

from ..models import DataManagementPlan as DMP
from ..models import Dataset
from ..util import create_new_record, distribution_matches_us, \
    fetch_unassigned_record, is_identifier_type_allowed, \
    translate_person_details


def get_matching_converter(
    distribution_dict: dict, dataset_dict: dict, dmp_dict: dict
) -> "BaseRecordConverter":
    """TODO."""
    for converter in app.config["MADMP_RECORD_CONVERTERS"]:
        if converter.matches(distribution_dict, dataset_dict, dmp_dict):
            return converter

    return app.config["MADMP_FALLBACK_RECORD_CONVERTER"]


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


def convert_dmp(madmp_dict: dict) -> List:
    """Map the maDMP's dictionary to a number of Invenio RDM Records."""
    records = []

    contact = map_contact(madmp_dict.get("contact", {}))
    contribs = list(map(map_contributor, madmp_dict.get("contributor", [])))
    creators = list(map(map_creator, madmp_dict.get("contributor", [])))
    dmp_id = madmp_dict.get("dmp_id", {}).get("identifier")
    dmp = DMP.get_by_dmp_id(dmp_id) or DMP(dmp_id=dmp_id)

    for dataset in madmp_dict.get("dataset", []):

        distribs = matching_distributions(dataset)
        if not distribs:
            # our repository is not listed as host for any of the distributions

            if not dataset.get("distribution"):
                # the dataset doesn't have any distributions specified... weird
                # TODO how do we want to handle this case?
                pass

            else:
                # there are distributions, but just not in our repo: ignore
                pass

        else:

            # we're not interested in datasets without deposit in Invenio
            # TODO: to be unique, we need the dataset_id identifier and type,
            #       which translate to pid_value and pid_type (the latter might
            #       require some mapping) -- then, PID provides a method
            #       PID.get(pid_type, pid_value)
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

            for distrib in distribs:
                # iterate over all dataset[].distribution[] elements that match
                # our repository, and create a record for each distribution
                # note: is expected to be at most one item, but if there are
                #       multiple matching items this is probably assumed
                #       (e.g. same dataset saved in our repo, in different
                #        formats)

                converter = get_matching_converter(
                    distrib, dataset, madmp_dict
                )

                if converter is None:
                    raise LookupError(
                        "no matching converter registered for dataset: %s"
                        % dataset
                    )

                record = converter.convert_dataset(
                    distrib,
                    dataset,
                    madmp_dict,
                    creators=creators,
                    contributors=contribs,
                    contact=contact,
                )

                records.append(record)

            ds = Dataset.get_by_dataset_id(dataset_id) or Dataset(
                dataset_id=dataset_id
            )

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
                    rec = create_new_record(records[0])

                    ds.record_pid = PID.query.filter(
                        PID.object_uuid == rec.id
                    ).first()

    # TODO commit DB session & index created drafts
    return dmp
