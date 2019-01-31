# test the functionality of generating a map of the structure of the BIDS
# folder

import tempfile
import os.path as op
import shutil
import xml.etree.ElementTree as ET

from BIDSHandler import BIDSTree

TESTPATH1 = 'data/BIDSTEST1'


def test_generate_xml():
    # Generate an xml mapping of the BDIS folder structure.
    with tempfile.TemporaryDirectory() as tmp:
        # copy the dst to a temp folder.
        shutil.copytree(TESTPATH1, op.join(tmp, 'BIDSTEST1'))
        folder = BIDSTree(op.join(tmp, 'BIDSTEST1'))
        folder.generate_map(op.join(tmp, 'map.xml'))

        tree = ET.ElementTree()
        tree.parse(op.join(tmp, 'map.xml'))
        # find the first project.
        proj = tree.find('Project')
        assert proj.attrib['ID'] == 'test1'
        subj = proj.find('Subject')
        assert subj.attrib['ID'] == '1'
        assert subj.attrib['sex'] == 'F'
        sess = subj.find('Session')
        assert sess.attrib['ID'] == '1'
        scan = sess.find('Scan')
        assert (scan.attrib['path'] ==
                'meg\\sub-1_ses-1_task-resting_run-1_meg\\sub-1_ses-1_task-resting_run-1_meg.con')  # noqa
