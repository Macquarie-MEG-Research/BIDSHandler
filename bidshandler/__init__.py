"""API for handling folders containing BIDS formatted data."""

__version__ = '0.3dev0'
name = "BIDSHandler"  # noqa

from .bidstree import BIDSTree  # noqa
from .project import Project  # noqa
from .subject import Subject  # noqa
from .session import Session  # noqa
from .scan import Scan  # noqa
from .bidserrors import (NoProjectError, NoSubjectError, NoSessionError,  # noqa
                         NoScanError, IDError, MappingError, AssociationError)
from .utils import download_test_data  # noqa