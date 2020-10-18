"""Interface and default implementations for RecordConverters.

RecordConverters are used to parse DMPs (respectively, datasets) into Records.
Different concrete RecordConverters can be used to parse datasets into different types
of Records (respectively, Records with different metadata models).
Custom RecordConverters should be added to the MADMP_RECORD_CONVERTERS configuration
item.
Whenever a matching dataset is about to be converted, the first matching RecordConverter
from this list (in order of definition) will be selected to perform the conversion.
"""

from .base import BaseRecordConverter
from .rdm_records import RDMRecordConverter

__all__ = ["BaseRecordConverter", "RDMRecordConverter"]
