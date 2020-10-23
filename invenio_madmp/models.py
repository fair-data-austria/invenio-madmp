# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 FAIR Data Austria.
#
# Invenio-DMP is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Database models for Data Management Plans."""

import uuid
from typing import List, Optional

from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from invenio_rdm_records.models import BibliographicRecordDraft
from invenio_records import Record
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_utils.types import UUIDType

from .signals import (
    dataset_created,
    dataset_deleted,
    dataset_record_pid_changed,
    dmp_created,
    dmp_dataset_added,
    dmp_dataset_removed,
    dmp_deleted,
)

datamanagementplan_dataset = db.Table(
    "dmp_datamanagementplan_dataset",
    db.Column("dmp_id", UUIDType, db.ForeignKey("dmp_datamanagementplan.id")),
    db.Column("dataset_id", UUIDType, db.ForeignKey("dmp_dataset.id")),
)


class DataManagementPlan(db.Model):
    """Data Management Plan.

    Stores the external ID for the DMP, to enable querying for it in the
    DMP tool.
    """

    __tablename__ = "dmp_datamanagementplan"
    __versioned__ = {"versioning": False}

    id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )
    """The internal identifier."""

    dmp_id = db.Column(
        db.String,
        nullable=False,
        unique=True,
    )
    """The dmp_id used to identify the DMP in the DMP tool."""

    datasets = db.relationship(
        "Dataset", secondary=datamanagementplan_dataset, back_populates="dmps"
    )

    def add_dataset(self, dataset: "Dataset", emit_signal=True):
        """TODO."""
        self.datasets.append(dataset)
        if emit_signal:
            dmp_dataset_added.send(self, dmp=self, dataset=dataset)

    def delete(self, emit_signal=True, commit=True):
        """Delete the DMP, but do not delete the datasets."""
        for ds in self.datasets:
            ds.dmps.remove(self)

        db.session.delete(self)

        if emit_signal:
            dmp_deleted.send(self, dmp=self)

        if commit:
            db.session.commit()

    @classmethod
    def get_by_dmp_id(cls, dmp_id: str) -> Optional["DataManagementPlan"]:
        """Get the dataset with the given dmp_id."""
        return cls.query.filter(cls.dmp_id == dmp_id).one_or_none()

    @classmethod
    def get_by_record(cls, record: Record) -> List["DataManagementPlan"]:
        """Get all DMPs using the given Record in a Dataset."""
        dataset = Dataset.get_by_record(record)

        if dataset is not None:
            return dataset.dmps

        return []

    @classmethod
    def get_by_record_pid(
        cls, record_pid: PersistentIdentifier
    ) -> List["DataManagementPlan"]:
        """Get all DMPs using the Record with the given PID in a Dataset."""
        dataset = Dataset.get_by_record_pid(record_pid)

        if dataset is not None:
            return dataset.dmps

        return []

    @classmethod
    def create(
        cls,
        dmp_id: str,
        datasets: List["Dataset"] = None,
        emit_signal: bool = True,
    ) -> "DataManagementPlan":
        """Create and store a DMP with the given properties."""
        dmp = None

        try:
            if not datasets:
                datasets = []
            elif isinstance(datasets, Dataset):
                # if the argument is a single Dataset, put it in a new list
                datasets = [datasets]

            with db.session.begin_nested():
                dmp = cls(
                    dmp_id=dmp_id,
                )
                dmp.datasets.extend(datasets)
                db.session.add(dmp)

        except IntegrityError:
            # TODO probably indicates a duplicate entry
            raise

        if emit_signal:
            dmp_created.send(cls, dmp=dmp)

        return dmp


class Dataset(db.Model):
    """Dataset as defined in a Data Management Plan.

    Stores the external ID for the dataset, to enable querying for it in the
    DMP tool.
    """

    __tablename__ = "dmp_dataset"
    __versioned__ = {"versioning": False}

    id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )
    """The internal identifier."""

    dataset_id = db.Column(
        db.String,
        nullable=False,
        unique=True,
    )
    """The dataset_id used to identify the dataset in the DMP tool."""

    dmps = db.relationship(
        "DataManagementPlan",
        secondary=datamanagementplan_dataset,
        back_populates="datasets",
    )

    # this is nullable b/c we also want to have knowledge about datasets that
    # do not have a distribution in Invenio (yet)
    # they can be used at deposit to create a new distribution for a dataset
    record_pid_id = db.Column(
        db.Integer,
        db.ForeignKey(PersistentIdentifier.id),
        unique=True,
    )

    record_pid = db.relationship(
        PersistentIdentifier,
        foreign_keys=[record_pid_id],
    )

    @property
    def has_record(self) -> bool:
        """Check if this Dataset has a Record assigned."""
        # since accessing the 'record' property may be expensive, we try
        # to minimize the cost of this function by checking the
        # 'record_pid_id' first, which does not require joins
        if self.record_pid_id is None or self.record_pid is None:
            return False
        elif self.record is None:
            return False
        else:
            return True

    @property
    def is_zombie(self) -> bool:
        """Check if this Dataset is a zombie (i.e. it has a dangling PID)."""
        return self.record_pid_id is not None and self.record is None

    @property
    def record(self) -> Optional[Record]:
        """Get the Record associated with this Dataset."""
        if self.record_pid is None:
            return None

        record = None
        record_uuid = self.record_pid.get_assigned_object()
        for api_cls in (Record, BibliographicRecordDraft):
            try:
                record = api_cls.get_record(record_uuid)
            except NoResultFound:
                continue
            else:
                # no exception means that we found a record
                break

        return record

    @record.setter
    def record(self, record: Record, emit_signal=True):
        old_pid = self.record_pid
        rec_id = record.id
        pids = PersistentIdentifier.query.filter_by(object_uuid=rec_id).all()
        # TODO make the function for fetching the "best" PID configurable
        pid = pids[0]
        # TODO emit a signal that the record has been changed; will be useful
        #      for detecting updates to be sent to the DMP Tool
        self.record_pid = pid

        if emit_signal:
            dataset_record_pid_changed.send(
                self,
                dataset=self,
                old_record=old_record,
                old_pid=old_pid,
                new_record=record,
                new_pid=pid,
            )

    def delete(self, emit_signal=True, commit=True):
        """Delete the dataset, but do not delete associated DMPs or records."""
        for dmp in self.dmps:
            dmp.datasets.remove(self)

        db.session.delete(self)

        if commit:
            db.session.commit()

        if emit_signal:
            dataset_deleted.send(self, dataset=self)

    @classmethod
    def get_by_dataset_id(cls, dataset_id: str) -> Optional["Dataset"]:
        """Get the dataset with the given dataset_id."""
        return cls.query.filter(cls.dataset_id == dataset_id).one_or_none()

    @classmethod
    def get_by_record(cls, record: Record) -> Optional["Dataset"]:
        """Get the associated Dataset for the given Record."""
        # TODO: a record may have multiple PIDs, and the Dataset is only
        #       associated with one of these PIDs
        pid = PersistentIdentifier.query.filter(
            PersistentIdentifier.object_uuid == record.id
        ).first()

        if pid is None:
            return None

        return cls.get_by_record_pid(pid)

    @classmethod
    def get_by_record_pid(cls, record_pid: PersistentIdentifier) -> Optional["Dataset"]:
        """Get the associated Dataset for the Record with the given PID."""
        if isinstance(record_pid, PersistentIdentifier):
            record_pid_id = record_pid.id
        else:
            record_pid_id = record_pid

        return cls.query.filter(cls.record_pid_id == record_pid_id).first()

    @classmethod
    def get_zombies(cls) -> List["Dataset"]:
        """Get all Datasets that are associated with non-existing records."""
        return [
            ds
            for ds in cls.query.filter(cls.record_pid_id != None)  # noqa
            if ds.record is None
        ]

    @classmethod
    def get_orphans(cls, include_zombies: bool = False) -> List["Dataset"]:
        """Get all Datasets that don't have an associated record."""
        if include_zombies:
            # TODO
            return []
        else:
            return cls.query.filter(cls.record_pid_id == None).all()  # noqa

    @classmethod
    def create(
        cls,
        dataset_id: str,
        record_pid: PersistentIdentifier,
        dmps: List[DataManagementPlan] = None,
        emit_signal: bool = True,
    ) -> "Dataset":
        """Create and store a Dataset with the given properties."""
        dataset = None

        try:
            record_pid_id = record_pid
            if isinstance(record_pid, PersistentIdentifier):
                record_pid_id = record_pid.id

            if not dmps:
                dmps = []
            elif isinstance(dmps, DataManagementPlan):
                # if the argument is a single DMP, put it in a new list
                dmps = [dmps]

            with db.session.begin_nested():
                dataset = cls(
                    dataset_id=dataset_id,
                    record_pid_id=record_pid_id,
                )
                dataset.dmps.extend(dmps)
                db.session.add(dataset)

        except IntegrityError:
            # TODO probably indicates a duplicate entry
            raise

        if emit_signal:
            dataset_created.send(cls, dataset=dataset)

        return dataset

    def __eq__(self, other: "Dataset") -> bool:
        """Check if this Dataset is equal to the other."""
        if not isinstance(other, self.__class__):
            return False
        elif self is other or self.id == other.id:
            return True

        return (
            self.dataset_id == other.dataset_id
            and self.record_pid_id == other.record_pid_id
        )
