"""Base classes for conversions between maDMP dictionaries and Records."""

from flask_principal import Identity
from invenio_drafts_resources.records import Draft
from invenio_records.api import Record


class BaseRecordConverter:
    """Converter between datasets/distributions in maDMPs and Records in Invenio."""

    def matches_dataset(self, dataset_dict: dict, dmp_dict: dict = None) -> bool:
        """Check if this converter is suitable for the specified maDMP dataset."""
        raise NotImplementedError

    def matches_record(self, record: Record) -> bool:
        """Check if this converter is suitable for the specified Record."""
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
        """Convert the maDMP dataset dictionary to a Record (or Draft).

        :param distribution_dict: The distribution which to convert to a Record.
        :param dataset_dict: The dataset dictionary to which the distribution belongs.
        :param dmp_dict: The dmp dictionary in which the dataset is defined.
        :param contact: The contact person's mail address.
        :param creators: The list of creators, as defined in the maMDP.
        :param contributors: The list of contributors, as defined in the maDMP.
        :return: The dictionary to be used as metadata for the Record.
        :rtype: dict
        """
        raise NotImplementedError

    def convert_record(self, record: Record) -> dict:
        """Convert the Record into a maDMP dataset distribution dictionary."""
        raise NotImplementedError

    def get_dataset_metadata_model(self, record: Record = None) -> dict:
        """Get the RDA DMP metadata property used by the Record or this Converter.

        If no record is specified, the metadata model for which this Converter matches
        will be returned in the RDA DMP format.

        Example:
            {
                "description": "Datacite-based metadata model used by Invenio RDM",
                "language": "eng",
                "metadata_standard_id": {
                    "identifier": https://schema.datacite.org/meta/kernel-4.3/",
                    "type": "url"
                }
            }

        :param record: The Record whose metadata model to report.
        :return: The metadata model used by the Record or Converter in RDA DMP format.
        :rtype: dict
        """
        raise NotImplementedError

    def create_record(self, record_data: dict, identity: Identity) -> Record:
        """Create a new Record (or Draft) from the specified metadata.

        :param record_data: The metadata to be used for the new Record or Draft.
        :param identity: The identity to be used for checking the creation permissions.
        :return: The created Record.
        :rtype: Record
        """
        raise NotImplementedError

    def is_draft(self, record: Record) -> bool:
        """Check if the specified object is a suitable Record."""
        return isinstance(record, Draft)

    def is_record(self, record: Record) -> bool:
        """Check if the specified object is a suitable Draft."""
        return isinstance(record, Record)

    def update_record(
        self,
        original_record: Record,
        new_record_data: dict,
        identity: Identity,
    ) -> Record:
        """Update the metadata of the specified Record with the new data.

        :param original_record: The Record whose metadata should be updated.
        :param new_records_data: The new (partial) metadata to be used.
        :param identity: The identity to be used for checking the update permissions.
        :return: The updated Record.
        :rtype: Record
        """
        original_record.update(new_record_data)
        return original_record.commit()
