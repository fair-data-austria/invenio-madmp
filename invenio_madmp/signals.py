"""Signals for Invenio-maDMP."""

from blinker import Namespace

_signals = Namespace()

record_changed = _signals.signal("record-changed")
dataset_changed = _signals.signal("dataset-changed")
dmp_changed = _signals.signal("dmp-changed")
