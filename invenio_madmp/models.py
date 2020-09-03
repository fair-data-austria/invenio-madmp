# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-DMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Database models for Data Management Plans."""

import uuid

from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata, RecordMetadataBase
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_utils.types import UUIDType
from typing import Iterable


class DataManagementPlan(db.Model):
    """Data Management Plan.

    Stores the ID for the DMP, to enable querying for it in the DMP tool.
    """

    __tablename__ = "dmp_datamanagementplan"
    __versioned__ = {"versioning": False}

    id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )

    dmp_id = db.Column(
        db.String,
        unique=True,
    )

    @classmethod
    def query_by_record(cls, record) -> Iterable["DataManagementPlanRecord"]:
        pid = PersistentIdentifier.query.filter(
            PersistentIdentifier.object_uuid == record.id
        ).first()

        if pid is None:
            return None

        return cls.query_by_record_pid(pid)

    @classmethod
    def query_by_record_pid(cls, record_pid) -> Iterable["DataManagementPlan"]:
        return [dmp_rec.dmp for dmp_rec in DataManagementPlanRecord.query_by_record_pid(record_pid, return_list=False)]


class DataManagementPlanRecord(db.Model, RecordMetadataBase):
    """Relationship model between DataManagementPlans and Records."""

    __tablename__ = "dmp_datamanagementplan_record"
    __table_args__ = (
        db.Index(
            "uidx_datamanagementplan_record_pid",
            "dmp_id", "record_pid_id",
            unique=True
        ),
        {"extend_existing": True},
    )
    __versioned__ = {"versioning": False}

    dmp_id = db.Column(
        UUIDType,
        db.ForeignKey(DataManagementPlan.id),
        nullable=False,
    )

    record_pid_id = db.Column(
        db.Integer,
        db.ForeignKey(PersistentIdentifier.id),
        nullable=False
    )

    dmp = db.relationship(
        DataManagementPlan,
        foreign_keys=[dmp_id],
    )

    record_pid = db.relationship(
        PersistentIdentifier,
        foreign_keys=[record_pid_id],
    )

    @property
    def record(self):
        return RecordMetadata.query.get(self.record_pid.get_assigned_object())

    @classmethod
    def query_by_record(cls, record) -> Iterable["DataManagementPlanRecord"]:
        pid = PersistentIdentifier.query.filter(
            PersistentIdentifier.object_uuid == record.id
        ).first()

        if pid is None:
            return None

        return cls.query_by_record_pid(pid)

    @classmethod
    def query_by_record_pid(cls, record_pid, return_list: bool = True) -> Iterable["DataManagementPlanRecord"]:
        if isinstance(record_pid, PersistentIdentifier):
            record_pid_id = record_pid.id
        else:
            record_pid_id = record_pid

        query = cls.query.filter(cls.record_pid_id == record_pid_id)

        return query.all() if return_list else query

    @classmethod
    def create(cls, dmp_id, record_pid_id):
        obj = None

        try:
            with db.session.begin_nested():
                obj = cls(dmp_id=dmp_id, record_pid_id=record_pid_id)
                db.session.add(obj)
        except IntegrityError:
            # TODO
            raise

        return obj

    @classmethod
    def delete(cls, dmp_record):
        with db.session.begin_nested():
            db.session.delete(dmp_record)
