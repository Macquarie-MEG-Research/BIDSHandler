# test the functionality of adding one BIDS object into another

import tempfile
import os.path as op

from BIDSHandler import (BIDSFolder, Project, Subject, Session, Scan,
                         AssociationError)

TESTPATH1 = 'data/test1'
TESTPATH2 = 'data/test2'


def test_scan_to_session():
    with tempfile.TemporaryDirectory() as tmp:
        assert op.exists(tmp)


def test_scan_to_subject():
    pass


def test_scan_to_project():
    pass


def test_scan_to_bidsfolder():
    with tempfile.TemporaryDirectory() as tmp:
        assert op.exists(tmp)


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
    with tempfile.TemporaryDirectory() as tmp:
        dest_bf = BIDSFolder(tmp, False)
        src_bf = BIDSFolder(TESTPATH2)
        dest_bf.add(src_bf)
        assert len(dest_bf.projects) == 1
        assert dest_bf.project('WS001').subject('1').age == 2.0
