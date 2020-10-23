"""Signals for Invenio-MaDMP."""

from blinker import Namespace

_signals = Namespace()

dataset_created = _signals.signal("dataset-created")
dataset_deleted = _signals.signal("dataset-deleted")
dataset_record_pid_changed = _signals.signal("dataset-record-pid-changed")

dmp_created = _signals.signal("dmp-created")
dmp_deleted = _signals.signal("dmp-deleted")
dmp_dataset_added = _signals.signal("dmp-dataset-added")
dmp_dataset_removed = _signals.signal("dmp-dataset-removed")
