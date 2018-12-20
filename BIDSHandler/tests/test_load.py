# test various aspects of loading BIDS folders

import tempfile
import os.path as op
import shutil
#import pytest

from BIDSHandler import BIDSTree

TESTPATH1 = 'data/BIDSTEST1'
TESTPATH2 = 'data/BIDSTEST2'


def test_containment():
    with tempfile.TemporaryDirectory() as tmp:
        # copy the dst to a temp folder
        shutil.copytree(TESTPATH2, op.join(tmp, 'BIDSTEST2'))
        src_bf = BIDSTree(TESTPATH1)
        dst_bf = BIDSTree(op.join(tmp, 'BIDSTEST2'))

        proj = src_bf.project('test1')
        subj = proj.subject('1')
        sess = subj.session('1')
        scan = sess.scan(task='resting', run='1')
        assert subj in dst_bf.project('test1')
        assert sess in dst_bf.project('test1').subject('1')
        assert scan in dst_bf.project('test1').subject('1').session('1')


def test_print():
    # test printing the projects
    # (this is basically just to get the coverage up...)
    src_bf = BIDSTree(TESTPATH1)
    proj = src_bf.project('test1')
    subj = proj.subject('1')
    sess = subj.session('1')
    scan = sess.scan(task='resting', run='1')
    print(src_bf)
    print(proj)
    print(subj)
    print(sess)
    print(scan)
