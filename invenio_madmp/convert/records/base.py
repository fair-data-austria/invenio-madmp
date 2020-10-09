"""TODO.

RecordConverters are used to parse DMPs (respectively, datasets) into Records.
Different concrete RecordConverters can be used to parse datasets into
different types of Records (respectively, Records with different metadata
models).
"""

from flask_principal import Identity
from invenio_drafts_resources.drafts import DraftBase
from invenio_records.api import Record


class BaseRecordConverter:
    """TODO."""

    def matches_dataset(self, dataset_dict: dict, dmp_dict: dict = None) -> bool:
        """TODO."""
        raise NotImplementedError

    def matches_record(self, record: Record) -> bool:
        """TODO."""
        return self.is_draft(record) or self.is_record(record)

    def convert_dataset(
        self,
        distribution_dict: dict,
        dataset_dict: dict,
        dmp_dict: dict,
        contact=None,
        creators=None,
        contributors=None,
    ) -> dict:
        """TODO."""
        raise NotImplementedError

    def create_record(self, record_data: dict, identity: Identity) -> Record:
        """TODO."""
        raise NotImplementedError

    def is_draft(self, record: Record) -> bool:
        """TODO."""
        return isinstance(record, DraftBase)

    def is_record(self, record: Record) -> bool:
        """TODO."""
        return isinstance(record, Record)

    def update_record(
        self,
        original_record: Record,
        new_record_data: dict,
        identity: Identity,
    ) -> Record:
        """TODO."""
        original_record.update(new_record_data)
        return original_record.commit()


# note: only the logic directly linked to record parsing needs to be
#       customizable for different metadata models; the general framework
#       (with logic such as checking if the DMP contains datasets that are
#        relevant for us, by checking for matching distributions) should
#       stay the same
