# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-DMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Database models for Data Management Plans."""

import uuid

from invenio_db import db
from invenio_records.models import RecordMetadata
from sqlalchemy import event
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils.types import UUIDType

# we need to explicitly define a mutilated version of the otherwise
# auto-generated table that links DMPs with record versions,
# b/c otherwise, we are likely to run into a lot of 'unique violation' or
# 'foreign key violation' errors, because invenio creates a new
# record version every time we add a record to a DMP
dmp_datamanagementplan_records_version = db.Table(
    "dmp_datamanagementplan_records_version",
    db.Column("dmp_id", UUIDType, db.ForeignKey("dmp_datamanagementplan.id")),
    db.Column("record_id", UUIDType),
    db.Column("transaction_id", db.BigInteger),
    db.Column("end_transaction_id", db.BigInteger),
    db.Column("operation_type", db.SmallInteger),
)

dmp_datamanagementplan_records = db.Table(
    "dmp_datamanagementplan_records",
    db.Column("dmp_id", UUIDType, db.ForeignKey("dmp_datamanagementplan.id")),
    db.Column("record_id", UUIDType, db.ForeignKey("records_metadata.id"))
)


class DataManagementPlan(db.Model):
    """Data Management Plan.

    Stores the ID for the DMP, to enable querying for it in the DMP tool.
    """

    __tablename__ = "dmp_datamanagementplan"

    id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )

    dmp_id = db.Column(
        db.String,
        unique=True,
    )

    records = db.relationship(
        RecordMetadata,
        secondary=dmp_datamanagementplan_records,
        lazy="dynamic",
        backref=db.backref(
            "dmps",
            lazy="dynamic",
        )
    )
