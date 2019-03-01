# test the functionality of adding one BIDS object into another

import tempfile
import os.path as op
import shutil

import pytest

from bidshandler import BIDSTree, AssociationError
from bidshandler.constants import test_path

testpath = test_path()
TESTPATH1 = op.join(testpath, 'BIDSTEST1')
TESTPATH2 = op.join(testpath, 'BIDSTEST2')


def test_add_new_project_recursively():
    # Add a scan existing in a project that doesn't exist in the dst folder
    # This will recursively add the project, subject and session.
    with tempfile.TemporaryDirectory() as tmp:
        # copy the dst to a temp folder
        shutil.copytree(TESTPATH2, op.join(tmp, 'BIDSTEST2'))
        src_bt = BIDSTree(TESTPATH1)
        dst_bt = BIDSTree(op.join(tmp, 'BIDSTEST2'))
        scan = src_bt.project('test2').subject('3').session('1').scan(
            task='resting', run='1')
        assert scan.emptyroom is not None
        dst_bt.add(scan)
        # make sure the project was added
        assert len(dst_bt.projects) == 2
        assert op.exists(dst_bt.project('test2').readme)
        assert op.exists(dst_bt.project('test2').description)
        # make sure the subject was added and the empty room data was too
        assert len(dst_bt.project('test2').subjects) == 2
        # make sure the scan was added
        scans_tsv = dst_bt.project('test2').subject('3').session('1').scans_tsv
        assert op.exists(scans_tsv)
        dst_bt.project('test2').subject('emptyroom')


def test_merge_bidstrees():
    # Test completely merging one BIDS folder into another.
    with tempfile.TemporaryDirectory() as tmp:
        # copy the dst to a temp folder
        shutil.copytree(TESTPATH2, op.join(tmp, 'BIDSTEST2'))
        src_bt = BIDSTree(TESTPATH1)
        dst_bt = BIDSTree(op.join(tmp, 'BIDSTEST2'))
        with pytest.warns(UserWarning):
            dst_bt.add(src_bt)
        assert len(dst_bt.projects) == 2
        # proj:test1, subj:2, sess: 1 will not have been merged
        assert (src_bt.project('test1').subject(2).session(2) not in
                dst_bt.project('test1').subject(2))
        # To rectify this, rename the folder-less session then re-add
        dst_bt.project('test1').subject(2).session('none').rename('1')
        dst_bt.project('test1').subject(2).add(
            src_bt.project('test1').subject(2).session(2))
        assert len(dst_bt.project('test1').subject(2).sessions) == 2
        # check that extra files are brought along
        sess = dst_bt.project('test2').subject(3).session(1)
        assert 'code' in sess.extra_data
        assert 'extradata' in sess.extra_data
        assert op.exists(op.join(sess.path, 'code', 'analysis.py'))
        assert op.exists(op.join(sess.path, 'extradata', 'extra.txt'))


def test_bidstree_to_bidstree():
    # Test writing one BIDSTree object to a new empty BIDSTree location.
    with tempfile.TemporaryDirectory() as tmp:
        dest_bf = BIDSTree(tmp, False)
        src_bt = BIDSTree(TESTPATH2)
        dest_bf.add(src_bt)
        assert len(dest_bf.projects) == 1
        assert dest_bf.project('test1').subject('1').subject_data['age'] == 2.0


def test_copy_errors():
    # Test trying to copy the wrong things into the wrong places.
    with tempfile.TemporaryDirectory() as tmp:
        # copy the dst to a temp folder
        shutil.copytree(TESTPATH2, op.join(tmp, 'BIDSTEST2'))
        src_bt = BIDSTree(TESTPATH1)
        dst_bt = BIDSTree(op.join(tmp, 'BIDSTEST2'))
        # try add one project to another with different ID's
        # try and add an object you shouldn't do:
        proj = src_bt.project('test1')
        with pytest.raises(TypeError):
            dst_bt.project('test1').subject('1').session('1').add(proj)
        with pytest.raises(TypeError):
            dst_bt.project('test1').subject('1').add(proj)
        with pytest.raises(TypeError):
            dst_bt.project('test1').add(src_bt)

        proj = src_bt.project('test2')
        sub = proj.subject('3')
        ses = sub.session('1')
        scan = ses.scan(task='resting', run='1')
        # try and add objects in the wrong project:
        with pytest.raises(ValueError):
            dst_bt.project('test1').add(proj)
        with pytest.raises(AssociationError):
            dst_bt.project('test1').add(sub)
        with pytest.raises(AssociationError):
            dst_bt.project('test1').add(ses)
        with pytest.raises(AssociationError):
            dst_bt.project('test1').add(scan)
        # try and add objects to the wrong subject:
        with pytest.raises(ValueError):
            dst_bt.project('test1').subject('1').add(sub)
        with pytest.raises(AssociationError):
            dst_bt.project('test1').subject('1').add(ses)
        with pytest.raises(AssociationError):
            dst_bt.project('test1').subject('1').add(scan)
        # try and add objects to the wrong session:
        with pytest.raises(ValueError):
            session = src_bt.project('test1').subject('1').session('2')
            dst_bt.project('test1').subject('1').session('1').add(session)
        with pytest.raises(AssociationError):
            dst_bt.project('test1').subject('1').session('1').add(scan)
