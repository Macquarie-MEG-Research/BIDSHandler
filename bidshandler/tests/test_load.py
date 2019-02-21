# test various aspects of loading BIDS folders

import tempfile
import os.path as op
import shutil
import pytest
from datetime import date

from bidshandler import (BIDSTree, NoSessionError, NoSubjectError,
                         NoProjectError, NoScanError)
from bidshandler.constants import test_path

testpath = test_path()
TESTPATH1 = op.join(testpath, 'BIDSTEST1')
TESTPATH2 = op.join(testpath, 'BIDSTEST2')
TESTPATH3 = op.join(testpath, 'bids-examples')


def test_containment():
    with tempfile.TemporaryDirectory() as tmp:
        # copy the dst to a temp folder
        shutil.copytree(TESTPATH2, op.join(tmp, 'BIDSTEST2'))
        src_bt = BIDSTree(TESTPATH1)
        dst_bt = BIDSTree(op.join(tmp, 'BIDSTEST2'))

        proj = src_bt.project('test1')
        subj = proj.subject('1')
        sess = subj.session('1')
        scan = sess.scan(task='resting', run='1')
        assert subj in dst_bt.project('test1')
        assert subj in dst_bt
        assert sess in dst_bt.project('test1').subject('1')
        assert sess in dst_bt.project('test1')
        assert sess in dst_bt
        assert scan in dst_bt.project('test1').subject(1).session(1)
        assert scan in dst_bt.project('test1').subject(1)
        assert scan in dst_bt.project('test1')
        assert scan in dst_bt
        assert scan.scan_type == 'meg'
        # check some emptyroom values
        sess2 = src_bt.project('test2').subject('3').session('1')
        assert sess2.scan(task='resting', run='1').emptyroom is not None

        # check the session date is correct
        assert sess.date == date(year=2018, month=10, day=26)

        # check regex works for scans
        with pytest.raises(Exception, match='Multiple'):
            sess.scan(run='1')
        assert len(sess.scan(run='1', return_all=True)) == 2
        assert sess.scan(task='rest') is not None

        # Make sure an error is raised if trying to test for an object that
        # connot possibly be in another.
        with pytest.raises(TypeError):
            assert 'cats' in src_bt
        with pytest.raises(TypeError):
            assert dst_bt in src_bt
        with pytest.raises(TypeError):
            assert dst_bt in proj
        with pytest.raises(TypeError):
            assert dst_bt in subj
        with pytest.raises(TypeError):
            assert dst_bt in sess

        # Check the paths for the associated `channels`, `events` and
        # `coordsystem` file are correct
        assert scan.coordsystem_json == op.normpath(op.join(testpath, 'BIDSTEST1/test1/sub-1/ses-1/meg/sub-1_ses-1_coordsystem.json'))  # noqa
        assert scan.events_tsv == op.normpath(op.join(testpath, 'BIDSTEST1/test1/sub-1/ses-1/meg/sub-1_ses-1_task-resting_run-1_events.tsv'))  # noqa
        assert scan.channels_tsv == op.normpath(op.join(testpath, 'BIDSTEST1/test1/sub-1/ses-1/meg/sub-1_ses-1_task-resting_run-1_channels.tsv'))  # noqa

        # Check that an error is raised when trying to get a specific object
        # that doesn't exist.
        with pytest.raises(NoProjectError):
            proj = src_bt.project('5')
        with pytest.raises(NoSubjectError):
            sess = proj.subject('5')
        with pytest.raises(NoSessionError):
            sess = subj.session('5')
        with pytest.raises(NoScanError):
            scan = sess.scan(task='fake')

        assert len(dst_bt['test1'].contained_files()) == 19

        # Check that some inherited properties correctly aren't defined for
        # objects they shouldn't be
        with pytest.raises(AttributeError):
            subj.projects
        with pytest.raises(AttributeError):
            sess.subjects
        with pytest.raises(AttributeError):
            scan.sessions


def test_large_dataset():
    # Test loading the bids-example dataset
    tree = BIDSTree(TESTPATH3)
    assert len(tree.projects) == 29
