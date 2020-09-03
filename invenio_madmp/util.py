#!/usr/bin/env python3
# TODO: make the functions used for mapping RDA Common Standard to
#       Invenio metadata model configurable
#       (because invenio doesn't necessarily use the current
#        Invenio-RDM-Records metadata model)
"""Utility functions for mapping RDA maDMPs to Invenio records."""

from datetime import datetime
from typing import List

from flask import current_app as app


def distribution_matches_us(distribution_dict):
    """Check if the 'host' of the distribution matches our repository."""
    host = distribution_dict.get("host", {})
    url_matches = (host.get("url", None) == app.config['MADMP_HOST_URL'])
    title_matches = (host.get("title", None) == app.config['MADMP_HOST_TITLE'])
    return url_matches or title_matches


def get_matching_distributions(dataset_dict):
    """Fetch all matching distributions from the dataset."""
    dists = []
    for dist in dataset_dict.get("distribution", []):
        if distribution_matches_us(dist):
            dists.append(dist)

    return dists


def map_access_right(distribution_dict):
    """Get the 'access_right' from the distribution."""
    return distribution_dict.get(
        "data_access",
        app.config['MADMP_DEFAULT_DATA_ACCESS']
    )


def map_contact(contact_dict):
    """Get the contact person's e-mail address."""
    return contact_dict.get("mbox", app.config['MADMP_DEFAULT_CONTACT'])


def map_resource_type(dataset_type_dict):
    """Map the resource type of the dataset."""
    # TODO mapping logic
    return {
        "type": "Other",  # TODO check vocabulary
        "subtype": dataset_type_dict.get("name", "Other")  # TODO check vocab
    }


def map_creator(creator_dict):
    """Map the DMP's creator(s) to the record's creator(s)."""
    # TODO creator = uploader?
    cid = creator_dict["contributor_id"]
    identifiers = {cid["type"]: cid["identifier"]}

    affiliations = []

    creator = {
        "name": creator_dict["name"],
        "type": "Personal",  # TODO ?
        # "given_name": None,  # TODO heuristics?
        # "family_name": None,  # TODO heuristics?
        "identifiers": identifiers,
        "affiliations": affiliations,
    }

    return creator


def map_title(dataset_dict):
    """Map the dataset's title to the record's title."""
    return {
        "title": dataset_dict.get("title", "[No Title]"),
        "type": "MainTitle",  # TODO check vocabulary
        "lang": dataset_dict.get(
            "language",
            app.config['MADMP_DEFAULT_LANGUAGE']
        ),
    }


def map_contributor(contributor_dict, role_idx=0):
    """Map the DMP's contributor(s) to the record's contributor(s)."""
    cid = contributor_dict["contributor_id"]
    identifiers = {cid["type"]: cid["identifier"]}

    affiliations = []

    contributor = {
        "name": contributor_dict["name"],
        "type": "Personal",  # TODO ?
        # "given_name": None,  # TODO heuristics?
        # "family_name": None,  # TODO heuristics?
        "identifiers": identifiers,
        "affiliations": affiliations,
        "role": contributor_dict["role"][role_idx],
    }

    return contributor


def map_language(dataset_dict):
    """Map the dataset's language to the record's language."""
    return dataset_dict.get("language", app.config['MADMP_DEFAULT_LANGUAGE'])


def map_license(license_dict):
    """Map the distribution's license to the record's license."""
    short_name = "BSD-3"  # TODO
    license_ = {
        "license": license_dict["name"],
        "uri": license_dict["license_ref"],
        "identifier": short_name,
        "scheme": short_name,
    }

    return license_


def map_description(dataset_dict):
    """Map the dataset's description to the record's description."""
    return {
        "description": dataset_dict.get("description", "[No Description]"),
        "type": "Other",  # TODO check vocabulary
        "lang": dataset_dict.get(
            "language",
            app.config['MADMP_DEFAULT_LANGUAGE']
        ),
    }


def parse_date(date_str):
    """Parse the given date string."""
    return datetime.fromisoformat(date_str)


def format_date(date):
    """Format the given date."""
    return date.isoformat()


def convert(madmp_dict) -> List:
    """Map the maDMP's dictionary to a number of Invenio RDM Records."""
    records = []

    contact = map_contact(madmp_dict.get("contact", {}))
    contribs = list(map(map_contributor, madmp_dict.get("contributor", [])))
    creators = list(map(map_creator, madmp_dict.get("contributor", [])))

    for dataset in madmp_dict.get("dataset", []):

        distribs = get_matching_distributions(dataset)
        if not distribs:
            # our repository is not listed as host for any of the distributions

            if not dataset["distribution"]:
                # the dataset doesn't have any distributions specified... weird
                # TODO how do we want to handle this case?
                pass

            else:
                # there are distributions, but just not in our repo: ignore
                pass

        else:
            for distrib in distribs:
                # iterate over all dataset[].distribution[] elements that match
                # our repository, and create a record for each distribution
                # note: is expected to be at most one item, but if there are
                #       multiple matching items this is probably assumed
                #       (e.g. same dataset saved in our repo, in different
                #        formats)

                resource_type = None
                types = dataset.get("type", [])
                if types:
                    resource_type = map_resource_type(types[0])

                access_right = map_access_right(distrib)
                titles = [map_title(dataset)]
                language = map_language(dataset)
                licenses = list(map(map_license, distrib.get("license", [])))
                descriptions = [map_description(dataset)]
                dates = []

                earliest_license_start = None
                for lic in distrib.get("license"):
                    lic_start = parse_date(lic["start_date"])

                    if earliest_license_start is None or \
                       lic_start < earliest_license_start:

                        earliest_license_start = lic_start

                record = {
                    "access_right": access_right,
                    "contact": contact,
                    "resource_type": resource_type,
                    "creators": creators,
                    "titles": titles,
                    "contributors": contribs,
                    "dates": dates,
                    "language": language,
                    "licenses": licenses,
                    "descriptions": descriptions,
                }

                if earliest_license_start is None or \
                   datetime.utcnow() < earliest_license_start:

                    # the earliest license start date is in the future:
                    # that means there's an embargo
                    fmt_date = format_date(earliest_license_start)
                    record["embargo_date"] = fmt_date

                # TODO
                record["_access"] = {
                    "files_restricted": False,
                    "metadata_restricted": False,
                }
                record["_owners"] = [1]
                record["_created_by"] = 1

                records.append(record)

    return records


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as dmap_json_file:
            dmap_dict = json.load(dmap_json_file)

        records = convert(dmap_dict["dmp"])
        records_json = json.dumps(records)
        print(records_json)
