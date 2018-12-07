class NoProjectError(Exception):
    pass


class NoSubjectError(Exception):
    pass


class NoSessionError(Exception):
    pass


class NoScanError(Exception):
    pass


class IDError(Exception):
    pass


class MappingError(Exception):
    """Raised when the folder structure doesn't match the BIDS standard."""
    pass


class AssociationError(Exception):
    """
    Raise when attempting to illegally add an object to a parent.
    Error message raised is "Cannot add a {child} from a different {parent}."
    """
    def __init__(self, child, parent):
        message = "Cannot add a {0} from a different {1}."
        self.message = message.format(child, parent)
