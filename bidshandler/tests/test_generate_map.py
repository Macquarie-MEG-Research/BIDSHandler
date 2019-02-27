# test the functionality of generating a map of the structure of the BIDS
# folder

import tempfile
import os.path as op
import shutil
import xml.etree.ElementTree as ET

from bidshandler import BIDSTree
from bidshandler.constants import test_path

TESTPATH1 = op.join(test_path(), 'BIDSTEST1')


def test_generate_xml():
    # Generate an xml mapping of the BDIS folder structure.
    with tempfile.TemporaryDirectory() as tmp:
        # copy the dst to a temp folder.
        shutil.copytree(TESTPATH1, op.join(tmp, 'BIDSTEST1'))
        folder = BIDSTree(op.join(tmp, 'BIDSTEST1'))
        folder.generate_map(op.join(tmp, 'map.xml'))

        tree = ET.ElementTree()
        tree.parse(op.join(tmp, 'map.xml'))
        assert len(tree.findall('Project')) == 2
        # find the `test1` project
        for _proj in tree.findall('Project'):
            if _proj.attrib['ID'] == 'test1':
                proj = _proj
        assert len(proj.findall('Subject')) == 2
        # find subject 1
        for _subj in proj.findall('Subject'):
            if _subj.attrib['ID'] == '1':
                subj = _subj
        assert subj.attrib['sex'] == 'F'
        assert len(subj.findall('Session')) == 2
        for _sess in subj.findall('Session'):
            if _sess.attrib['ID'] == '1':
                sess = _sess
        assert len(sess.findall('Scan')) == 2
        scan = None
        for _scan in sess.findall('Scan'):
            if (_scan.attrib['path'] ==
                    op.join(
                        'meg',
                        'sub-1_ses-1_task-resting_run-1_meg',
                        'sub-1_ses-1_task-resting_run-1_meg.con')):
                scan = _scan
        assert scan is not None
