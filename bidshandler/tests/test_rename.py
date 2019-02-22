# test the functionality of renaming folders

import tempfile
import os.path as op
import shutil
import os
import pandas as pd

from bidshandler import BIDSTree
from bidshandler.constants import test_path

testpath = test_path()
TESTPATH1 = op.join(testpath, 'BIDSTEST1')
TESTPATH2 = op.join(testpath, 'BIDSTEST2')


def test_rename():
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(TESTPATH1, op.join(tmp, 'BIDSTEST1'))
        src_bt = BIDSTree(op.join(tmp, 'BIDSTEST1'))

        # renaming a subject
        subj = src_bt.project('test1').subject(2)
        subj.rename('4')
        assert subj.ID == 'sub-4'
        for _, _, files in os.walk(subj.path):
            for fname in files:
                assert 'sub-2' not in fname
        sess = subj.session(2)
        assert 'sub-4' in sess.scans[0].raw_file

        # renaming a session
        sess.rename('3')
        assert sess.ID == 'ses-3'
        for _, _, files in os.walk(subj.path):
            for fname in files:
                assert 'ses-2' not in fname
        df = pd.read_csv(sess.scans_tsv, sep='\t')
        for row in df['filename']:
            assert 'ses-3' in row
            assert 'sub-4' in row

        # test renaming a folder-less session to have a session label
        shutil.copytree(TESTPATH2, op.join(tmp, 'BIDSTEST2'))
        src_bt = BIDSTree(op.join(tmp, 'BIDSTEST2'))

        sess = src_bt.project('test1').subject(2).session('none')
        orig_path = sess.path
        sess.rename('1')
        assert sess.path == op.join(orig_path, 'ses-1')
