# test the functionality of adding one BIDS object into another

import tempfile
import os.path as op


def test_scan_to_session():
    with tempfile.TemporaryDirectory() as tmp:
        assert op.exists(tmp)


def test_scan_to_subject():
    pass


def test_scan_to_project():
    pass


def test_scan_to_bidsfolder():
    pass


def test_session_to_session():
    pass


def test_session_to_subject():
    pass


def test_session_to_project():
    pass


def test_session_to_bidsfolder():
    pass


def test_subject_to_subject():
    pass


def test_subject_to_project():
    pass


def test_subject_to_bidsfolder():
    pass


def test_project_to_project():
    pass


def test_project_to_bidsfolder():
    pass


def test_bidsfolder_to_bidsfolder():
    pass
