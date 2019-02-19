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
        sess = subj.session(1)
        assert 'sub-4' in sess.scans[0].raw_file

        # renaming a session
        sess.rename('2')
        assert sess.ID == 'ses-2'
        for _, _, files in os.walk(subj.path):
            for fname in files:
                assert 'ses-1' not in fname
        df = pd.read_csv(sess.scans_tsv, sep='\t')
        for row in df['filename']:
            assert 'ses-2' in row
            assert 'sub-4' in row
