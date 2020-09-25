"""TODO.

RecordConverters are used to parse DMPs (respectively, datasets) into Records.
Different concrete RecordConverters can be used to parse datasets into
different types of Records (respectively, Records with different metadata
models).
"""

from invenio_records.api import Record


class BaseRecordConverter:
    """TODO."""

    def matches(self, dataset_dict: dict, dmp_dict: dict = None) -> bool:
        """TODO."""
        raise NotImplementedError

    def convert_dataset(
        self,
        distribution_dict: dict,
        dataset_dict: dict,
        dmp_dict: dict,
        contact=None,
        creators=None,
        contributors=None,
    ) -> Record:
        """TODO."""
        raise NotImplementedError


# note: only the logic directly linked to record parsing needs to be
#       customizable for different metadata models; the general framework
#       (with logic such as checking if the DMP contains datasets that are
#        relevant for us, by checking for matching distributions) should
#       stay the same
