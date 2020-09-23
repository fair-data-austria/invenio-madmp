# TODO: make the functions used for mapping RDA Common Standard to
#       Invenio metadata model configurable
#       (because invenio doesn't necessarily use the current
#        Invenio-RDM-Records metadata model)
"""Utility functions for mapping RDA maDMPs to Invenio records."""

from datetime import datetime
from typing import List

from flask import current_app as app
from invenio_pidstore.models import PersistentIdentifier as PID

from .models import DataManagementPlan as DMP
from .models import Dataset
from .util import create_new_record, distribution_matches_us, \
    fetch_unassigned_record, find_user, format_date, \
    is_identifier_type_allowed, parse_date, translate_dataset_type, \
    translate_license, translate_person_details


def matching_distributions(dataset_dict):
    """Fetch all matching distributions from the dataset."""
    return [
        dist
        for dist in dataset_dict.get("distribution", [])
        if distribution_matches_us(dist)
    ]


def map_access_right(distribution_dict):
    """Get the 'access_right' from the distribution."""
    return distribution_dict.get(
        "data_access", app.config["MADMP_DEFAULT_DATA_ACCESS"]
    )


def map_contact(contact_dict):
    """Get the contact person's e-mail address."""
    return contact_dict.get("mbox", app.config["MADMP_DEFAULT_CONTACT"])


def map_resource_type(dataset_dict):
    """Map the resource type of the dataset."""
    return translate_dataset_type(dataset_dict)


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


def map_title(dataset_dict):
    """Map the dataset's title to the record's title."""
    return {
        "title": dataset_dict.get("title", "[No Title]"),
        "type": "MainTitle",  # TODO check vocabulary
        "lang": dataset_dict.get(
            "language", app.config["MADMP_DEFAULT_LANGUAGE"]
        ),
    }


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


def map_language(dataset_dict):
    """Map the dataset's language to the record's language."""
    # note: both RDA-CS and Invenio-RDM-Records use ISO 639-3
    return dataset_dict.get("language", app.config["MADMP_DEFAULT_LANGUAGE"])


def map_license(license_dict):
    """Map the distribution's license to the record's license."""
    return translate_license(license_dict)


def map_description(dataset_dict):
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


def distribution_to_record(
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

    resource_type = map_resource_type(dataset_dict)
    access_right = map_access_right(distribution_dict)
    titles = [map_title(dataset_dict)]
    language = map_language(dataset_dict)
    licenses = list(map(map_license, distribution_dict.get("license", [])))
    descriptions = [map_description(dataset_dict)]
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
    emails = [contact] + [creator.get("mbox") for creator in contributor_list]
    users = [
        user
        for user in (find_user(email) for email in emails if email is not None)
    ]

    if None in users and False:  # TODO add config item instead of False
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


def convert(madmp_dict) -> List:
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

                record = distribution_to_record(
                    distrib,
                    dataset,
                    madmp_dict,
                    contact=contact,
                    creators=creators,
                    contributors=contribs,
                )
                records.append(record)

            ds = Dataset.get_by_dataset_id(dataset_id) or Dataset(
                dataset_id=dataset_id
            )

            if ds not in dmp.datasets:
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
