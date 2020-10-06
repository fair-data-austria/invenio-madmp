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
import shutil
import tempfile
import uuid

import pytest
from flask import Flask
from flask_babelex import Babel
from invenio_access import InvenioAccess
from invenio_accounts import InvenioAccounts
from invenio_config import InvenioConfigDefault
from invenio_db import InvenioDB, db
from invenio_indexer import InvenioIndexer
from invenio_pidrelations import InvenioPIDRelations
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.models import PersistentIdentifier as PID
from invenio_rdm_records.pid_manager import BibliographicPIDManager
from invenio_records import InvenioRecords
from invenio_records.api import Record
from invenio_search import InvenioSearch
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from invenio_madmp import InvenioMaDMP
from invenio_madmp.convert.records import RDMRecordConverter
from invenio_madmp.models import DataManagementPlan, Dataset


class DummyRDMRecordConverter(RDMRecordConverter):
    """Dummy record converter that doesn't index records."""

    def create_record(self, data, identity):
        """Create a draft, but don't index it."""
        service = self.record_service
        validated_data = service.data_validator.validate(data, partial=True)
        rec_uuid = uuid.uuid4()
        service.pid_manager.mint(record_uuid=rec_uuid, data=validated_data)
        draft = service.draft_cls.create(validated_data, id_=rec_uuid)

        db.session.commit()
        return draft


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
        MADMP_FALLBACK_RECORD_CONVERTER=DummyRDMRecordConverter(),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "SQLALCHEMY_DATABASE_URI", "sqlite://"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    Babel(app)
    InvenioConfigDefault(app)
    InvenioDB(app)
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
    u5 = datastore.create_user(
        email="CR@juve.it", password="pizza1234", active=True
    )
    u6 = datastore.create_user(
        email="cc@example.com", password="password", active=True
    )

    db.session.commit()
    return [u1, u2, u3, u4, u5, u6]


@pytest.fixture()
def example_data(base_app):
    """Create a collection of example records, datasets and DMPs."""
    records = []
    pid_manager = BibliographicPIDManager()
    rec_dir = os.path.join(os.path.dirname(__file__), "data", "records")

    # create some records from the example data
    for fn in sorted(f for f in os.listdir(rec_dir) if f.endswith(".json")):
        ffn = os.path.join(rec_dir, fn)
        with open(ffn, "r") as rec_file:
            data = json.load(rec_file)
            rec_uuid = uuid.uuid4()
            pid_manager.mint(record_uuid=rec_uuid, data=data)
            rec = Record.create(data, id_=rec_uuid)
            records.append(rec)

    # create some datasets
    datasets = []
    for i in range(7):
        ds_id = "dataset-%s" % (i + 1)

        rec = records[i]
        rec_pid = PID.get_by_object("recid", "rec", rec.id)

        ds = Dataset.create(ds_id, rec_pid)
        datasets.append(ds)
    unused_records = records[7:]

    # create some DMPs
    dss = datasets
    dmp1 = DataManagementPlan.create("dmp-1", [dss[0]])
    dmp2 = DataManagementPlan.create("dmp-2", [dss[0], dss[1], dss[2]])
    dmp3 = DataManagementPlan.create("dmp-3", [dss[2], dss[3]])
    dmp4 = DataManagementPlan.create("dmp-4", [dss[4], dss[5]])
    unused_datasets = [dss[6]]
    used_datasets = datasets[:6]

    return {
        "records": records,
        "unused_records": unused_records,
        "datasets": datasets,
        "used_datasets": used_datasets,
        "unused_datasets": unused_datasets,
        "dmps": [dmp1, dmp2, dmp3, dmp4],
    }
