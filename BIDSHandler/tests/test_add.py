# test the functionality of adding one BIDS object into another

import tempfile
import os.path as op
import shutil
import pytest

from BIDSHandler import BIDSTree, AssociationError

TESTPATH1 = 'data/BIDSTEST1'
TESTPATH2 = 'data/BIDSTEST2'


def test_add_new_project_recursively():
    # Add a scan existing in a project that doesn't exist in the dst folder
    # This will recursively add the project, subject and session.
    with tempfile.TemporaryDirectory() as tmp:
        # copy the dst to a temp folder
        shutil.copytree(TESTPATH2, op.join(tmp, 'BIDSTEST2'))
        src_bf = BIDSTree(TESTPATH1)
        dst_bf = BIDSTree(op.join(tmp, 'BIDSTEST2'))
        dst_bf.add(src_bf.project('test2').subject('3').session('1').scan(
            task='resting', run='1'))
        # make sure the project was added
        assert len(dst_bf.projects) == 2
        assert op.exists(dst_bf.project('test2').readme)
        assert op.exists(dst_bf.project('test2').description)
        # make sure the subject was added
        assert len(dst_bf.project('test1').subjects) == 1
        # make sure the scan was added
        scans_tsv = dst_bf.project('test2').subject('3').session('1').scans_tsv
        assert op.exists(scans_tsv)


def test_merge_bidstrees():
    # Test completely merging one BIDS folder into another.
    with tempfile.TemporaryDirectory() as tmp:
        # copy the dst to a temp folder
        shutil.copytree(TESTPATH2, op.join(tmp, 'BIDSTEST2'))
        src_bf = BIDSTree(TESTPATH1)
        dst_bf = BIDSTree(op.join(tmp, 'BIDSTEST2'))
        dst_bf.add(src_bf)
        assert len(dst_bf.projects) == 2
        raw = dst_bf.project('test1').subject('2').session('1').scan(
            task='restingstate', run='1').raw_file
        assert op.exists(raw)


def test_bidstree_to_bidstree():
    # Test writing one BIDSTree object to a new empty BIDSTree location.
    with tempfile.TemporaryDirectory() as tmp:
        dest_bf = BIDSTree(tmp, False)
        src_bf = BIDSTree(TESTPATH2)
        dest_bf.add(src_bf)
        assert len(dest_bf.projects) == 1
        assert dest_bf.project('test1').subject('1').subject_data['age'] == 2.0


def test_copy_errors():
    # Test trying to copy the wrong things into the wrong places.
    with tempfile.TemporaryDirectory() as tmp:
        # copy the dst to a temp folder
        shutil.copytree(TESTPATH2, op.join(tmp, 'BIDSTEST2'))
        src_bf = BIDSTree(TESTPATH1)
        dst_bf = BIDSTree(op.join(tmp, 'BIDSTEST2'))
        # try add one project to another with different ID's
        # try and add an object you shouldn't do:
        proj = src_bf.project('test1')
        with pytest.raises(TypeError):
            dst_bf.project('test1').subject('1').session('1').add(proj)
        with pytest.raises(TypeError):
            dst_bf.project('test1').subject('1').add(proj)
        with pytest.raises(TypeError):
            dst_bf.project('test1').add(src_bf)

        proj = src_bf.project('test2')
        sub = proj.subject('3')
        ses = sub.session('1')
        scan = ses.scan(task='resting', run='1')
        # try and add objects in the wrong project:
        with pytest.raises(ValueError):
            dst_bf.project('test1').add(proj)
        with pytest.raises(AssociationError):
            dst_bf.project('test1').add(sub)
        with pytest.raises(AssociationError):
            dst_bf.project('test1').add(ses)
        with pytest.raises(AssociationError):
            dst_bf.project('test1').add(scan)
        # try and add objects to the wrong subject:
        with pytest.raises(ValueError):
            dst_bf.project('test1').subject('1').add(sub)
        with pytest.raises(AssociationError):
            dst_bf.project('test1').subject('1').add(ses)
        with pytest.raises(AssociationError):
            dst_bf.project('test1').subject('1').add(scan)
        # try and add objects to the wrong session:
        with pytest.raises(ValueError):
            session = src_bf.project('test1').subject('1').session('2')
            dst_bf.project('test1').subject('1').session('1').add(session)
        with pytest.raises(AssociationError):
            dst_bf.project('test1').subject('1').session('1').add(scan)
