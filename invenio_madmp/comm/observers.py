"""Observer functions for DMP lifecycle signals.

The provided functions act as adapters between emitted DMP/dataset/record lifecycle
signals and the functions used for sending update notifications to the DMP tool.

Once they are connected to their signals, they will try to parse the required
information from the emitted signal (the presence of certain data is assumed)
and automatically create and send requests to the DMP tool.
"""

from ..models import Dataset
from .requests import (
    send_dataset_addition,
    send_distribution_deletion,
    send_distribution_update,
)


def prepare_sending_new_dataset(sender, **kwargs):
    """TODO."""
    print("dmp: new dataset, signal received")
    dmp = kwargs["dmp"]
    dataset = kwargs["dataset"]

    if dmp is not None and dataset is not None:
        send_dataset_addition(dmp=dmp, dataset=dataset, raise_exc=False)


def prepare_sending_deleted_dataset(sender, **kwargs):
    """TODO."""
    print("dataset: deleted, signal received")
    dataset = kwargs["dataset"]
    send_distribution_deletion(dataset=dataset, raise_exc=False)


def prepare_sending_distribution_deletion(sender, **kwargs):
    """TODO."""
    print("record: deleted, signal received")
    record = kwargs["record"]  # TODO check
    dataset = Dataset.get_by_record(record)

    if dataset is not None:
        # we use the record as keyword arg here, because going via the dataset may not
        # work -- since the record is deleted, dataset.record will likely return None
        send_distribution_deletion(record=record, raise_exc=False)


def prepare_sending_changed_dataset(sender, **kwargs):
    """TODO."""
    print("dataset: record pid changed, signal received")
    dataset = kwargs["dataset"]
    send_distribution_update(dataset=dataset, raise_exc=False)


def prepare_sending_distribution_update(sender, **kwargs):
    """TODO."""
    print("record: updated, signal received")
    record = kwargs["record"]  # TODO check
    dataset = Dataset.get_by_record(record)

    if dataset is not None:
        send_distribution_update(dataset=dataset, raise_exc=False)
