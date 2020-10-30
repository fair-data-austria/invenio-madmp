# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-maDMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

import json
import os
import os.path
import secrets
import shutil
import tempfile

import pytest
from flask import Flask
from flask_babelex import Babel
from flask_principal import Identity
from invenio_access import InvenioAccess
from invenio_access.permissions import any_user
from invenio_accounts import InvenioAccounts
from invenio_config import InvenioConfigDefault
from invenio_db import InvenioDB, db
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from invenio_rdm_records.models import BibliographicRecord
from invenio_rdm_records.services import BibliographicRecordService
from invenio_records import InvenioRecords
from invenio_search import InvenioSearch
from sqlalchemy_utils.functions import create_database, database_exists, drop_database

from invenio_madmp import InvenioMaDMP
from invenio_madmp.convert.records import RDMRecordConverter
from invenio_madmp.models import DataManagementPlan, Dataset


def create_record(data, identity, service):
    """Create a record using stripped-down logic from the RDM record service."""
    record = BibliographicRecord.create(data)

    for component in service.components:
        if hasattr(component, 'create'):
            component.create(identity, data=data, record=record)

    record.commit()

    if not record.is_published:
        record.register()

    return record


@pytest.fixture(scope="module")
def celery_config():
    """Override pytest-invenio fixture.

    TODO: Remove this fixture if you add Celery support.
    """
    return {}


@pytest.fixture()
def base_app(request):
    """Basic Flask application."""
    instance_path = tempfile.mkdtemp()
    app = Flask("testapp")
    app.config.update(
        MADMP_HOST_URL="https://test.invenio.cern.ch",
        MADMP_HOST_TITLE="Invenio",
        MADMP_FALLBACK_RECORD_CONVERTER=RDMRecordConverter(),
        SQLALCHEMY_DATABASE_URI=os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite://"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY=secrets.token_hex(20),
    )
    Babel(app)
    InvenioConfigDefault(app)
    InvenioDB(app)
    InvenioJSONSchemas(app)
    InvenioRecords(app)
    InvenioPIDStore(app)
    InvenioPIDRelations(app)
    InvenioAccounts(app)
    InvenioAccess(app)
    InvenioIndexer(app)
    InvenioSearch(app)
    InvenioMaDMP(app)

    with app.app_context():
        db_url = str(db.engine.url)
        if db_url != "sqlite://" and not database_exists(db_url):
            create_database(db_url)
        db.create_all()

    def teardown():
        with app.app_context():
            db_url = str(db.engine.url)
            db.session.close()
            if db_url != "sqlite://":
                drop_database(db_url)
            shutil.rmtree(instance_path)

    request.addfinalizer(teardown)
    app.test_request_context().push()

    return app


@pytest.fixture()
def example_madmps():
    """Dictionary with example maDMPs."""
    res = {}
    dirname = os.path.join(os.path.dirname(__file__), "data", "madmps")
    for fname in [f for f in os.listdir(dirname) if f.endswith("json")]:
        fbase = os.path.splitext(fname)[0]
        with open(os.path.join(dirname, fname), "r") as madmp_file:
            madmp_json = json.load(madmp_file)
            res[fbase] = madmp_json

    return res


@pytest.fixture()
def example_madmps_for_invenio(example_madmps):
    """Dictionary with example maDMPs with dataset distros in our Invenio."""
    for madmp in example_madmps.values():
        for ds in madmp["dmp"].get("dataset", []):
            for dist in ds.get("distribution", []):
                if "host" in dist:
                    dist["host"]["title"] = "Invenio"
                    dist["host"]["url"] = "https://test.invenio.cern.ch"

    return example_madmps


@pytest.fixture()
def example_madmps_for_invenio_with_datacite_metadata(example_madmps_for_invenio):
    """Dictionary with example maDMPs with dataset distros in our Invenio."""
    for madmp in example_madmps_for_invenio.values():
        for ds in madmp["dmp"].get("dataset", []):
            if "metadata" not in ds:
                ds["metadata"] = []

            has_datacite_metadata = False
            for metadata in ds.get("metadata", []):
                identifier = metadata.get("metadata_standard_id", {}).get("identifier")
                if "datacite.org" in identifier:
                    has_datacite_metadata = True

            if not has_datacite_metadata:
                datacite_metadata = {
                    "description": "Datacite Metadata Schema 4.3",
                    "language": "eng",
                    "metadata_standard_id": {
                        "identifier": "https://schema.datacite.org/meta/kernel-4.3/",
                        "type": "url",
                    },
                }

                ds["metadata"].append(datacite_metadata)

    return example_madmps_for_invenio


@pytest.fixture()
def example_madmps_for_invenio_requiring_users(example_madmps_for_invenio):
    """Only those example maDMPs that have datasets and contributors."""
    madmps = {}
    for name, madmp in example_madmps_for_invenio.items():
        dmp = madmp["dmp"]
        for ds in dmp.get("dataset", []):
            for dist in ds.get("distribution", []):
                if dist.get("host") is not None:
                    madmps[name] = madmp

    return madmps


@pytest.fixture()
def all_required_accounts(base_app):
    """All required user accounts for the example maDMPs."""
    datastore = base_app.extensions["security"].datastore
    u1 = datastore.create_user(
        email="TMiksa@sba-research.org", password="ilikecoffee", active=True
    )
    u2 = datastore.create_user(
        email="john.smith@tuwien.ac.at", password="tuwrulez", active=True
    )
    u3 = datastore.create_user(
        email="leo.messi@barcelona.com", password="gaudi4prez", active=True
    )
    u4 = datastore.create_user(
        email="robert@bayern.de", password="weisswurschtundbier", active=True
    )
    u5 = datastore.create_user(email="CR@juve.it", password="pizza1234", active=True)
    u6 = datastore.create_user(email="cc@example.com", password="password", active=True)

    db.session.commit()
    return [u1, u2, u3, u4, u5, u6]


@pytest.fixture()
def example_data(base_app):
    """Create a collection of example records, datasets and DMPs."""
    with db.session.no_autoflush:
        quiet = {"commit": False, "emit_signal": False}
        records = []
        rec_dir = os.path.join(os.path.dirname(__file__), "data", "records")
        service = BibliographicRecordService()
        identity = Identity(1)
        identity.provides.add(any_user)

        # create some records from the example data
        for fn in sorted(f for f in os.listdir(rec_dir) if f.endswith(".json")):
            ffn = os.path.join(rec_dir, fn)
            with open(ffn, "r") as rec_file:
                data = json.load(rec_file)
                rec = create_record(data, identity, service)
                records.append(rec)

        # create some datasets
        datasets = []
        for i in range(7):
            ds_id = "dataset-%s" % (i + 1)
            rec = records[i]
            rec_pid = rec.pid
            ds = Dataset.create(ds_id, rec_pid, **quiet)
            datasets.append(ds)

        unused_records = records[7:]

        # create some DMPs
        dss = datasets
        dmp1 = DataManagementPlan.create("dmp-1", [dss[0]], **quiet)
        dmp2 = DataManagementPlan.create("dmp-2", [dss[0], dss[1], dss[2]], **quiet)
        dmp3 = DataManagementPlan.create("dmp-3", [dss[2], dss[3]], **quiet)
        dmp4 = DataManagementPlan.create("dmp-4", [dss[4], dss[5]], **quiet)
        unused_datasets = [dss[6]]
        used_datasets = datasets[:6]

    db.session.commit()

    return {
        "records": records,
        "unused_records": unused_records,
        "datasets": datasets,
        "used_datasets": used_datasets,
        "unused_datasets": unused_datasets,
        "dmps": [dmp1, dmp2, dmp3, dmp4],
    }
