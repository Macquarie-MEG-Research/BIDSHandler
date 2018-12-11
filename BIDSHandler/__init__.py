"""API for handling folders containing BIDS formatted data."""

__version__ = '0.1.0'
name = "BIDSHandler"  # noqa

from .BIDSFolder import BIDSFolder  # noqa
from .Project import Project  # noqa
from .Subject import Subject  # noqa
from .Session import Session  # noqa
from .Scan import Scan  # noqa
from .BIDSErrors import (NoProjectError, NoSubjectError, NoSessionError,  # noqa
                         NoScanError, IDError, MappingError, AssociationError)
