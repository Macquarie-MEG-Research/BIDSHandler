# test the query functionality

import pytest

from BIDSHandler import BIDSTree

TESTPATH1 = 'data/BIDSTEST1'


def test_query():
    folder = BIDSTree(TESTPATH1)

    # query a BIDSTree object

    # query some subject information
    assert len(folder.query('subject', 'age', '=', 4)) == 1
    assert len(folder.query('subject', 'age', '>', 2)) == 2
    assert len(folder.query('subject', 'age', '>=', 2)) == 3
    assert len(folder.query('subject', 'sex', '=', 'M')) == 1
    assert len(folder.query('subject', 'sex', '!=', 'M')) == 2
    assert len(folder.query('subject', 'group', '=', 'autistic')) == 2
    with pytest.raises(ValueError, match='subject data'):
        folder.query('project', 'age', '=', '4')
    with pytest.raises(ValueError, match='subject data'):
        folder.query('session', 'sex', '=', 'M')
    with pytest.raises(ValueError, match='subject data'):
        folder.query('scan', 'group', '=', 'autistic')
    with pytest.raises(ValueError, match='Condition'):
        folder.query('subject', 'sex', '<', 'M')
    with pytest.raises(ValueError, match='Condition'):
        folder.query('subject', 'group', '>', 'test')

    # query some tasks
    assert len(folder.query('scan', 'task', '=', 'resting')) == 2
    # ask if any of the subjects has *any* tasks that aren't 'resting'
    assert (folder.query('subject', 'task', '!=', 'resting')[0] ==
            folder.project('test1').subject('1'))
    # ask if any of the subjects have not got a task called 'resting'
    assert (folder.query('subject', 'task', '!!=', 'resting')[0] ==
            folder.project('test1').subject('2'))
    with pytest.raises(ValueError, match='Condition'):
        folder.query('subject', 'task', '>', 'resting')

    # query the recording date
    ref_datetime = '2018-10-26T11:32:33'
    ref_date = '2018-10-26'
    assert len(folder.query('scan', 'rec_date', '=', ref_datetime)) == 1
    assert len(folder.query('scan', 'rec_date', '<=', ref_datetime)) == 4
    assert len(folder.query('scan', 'rec_date', '>', ref_datetime)) == 1
    assert len(folder.query('scan', 'rec_date', '=', ref_date)) == 5
    assert len(folder.query('session', 'rec_date', '=', ref_date)) == 4

    # query some data in the sidecar.json:
    assert len(folder.query('project', 'PowerLineFrequency', '=', 50)) == 2
    assert len(folder.query('subject', 'MiscChannelCount', '=', 93)) == 3
    assert len(folder.query('session', 'TaskName', '=', 'resting')) == 2
    assert len(folder.query('scan', 'RecordingDuration', '>=', 5)) == 5

    # query for number of subjects, sessions, or scans
    assert len(folder.query('project', 'subjects', '=', 2)) == 1
    assert len(folder.query('project', 'sessions', '!=', 3)) == 1
    assert len(folder.query('subject', 'sessions', '<', 2)) == 2
    assert len(folder.query('project', 'scans', '>', 4)) == 0
    assert len(folder.query('subject', 'scans', '<=', 2)) == 2
    assert len(folder.query('session', 'scans', '<', 2)) == 3

    # query a Project object:

    proj = folder.query('project', 'subjects', '=', 2)[0]
    assert len(proj.query('subject', 'sessions', '=', 2)) == 1
    assert len(proj.query('subject', 'group', '=', 'neurotypical')) == 1
    assert len(proj.query('session', 'scans', '<=', 3)) == 3

    # query a Subject object:

    subj = proj.query('subject', 'sessions', '=', 2)[0]
    assert len(subj.query('session', 'scans', '>=', 1)) == 2

    # perform a compound query:

    projs = folder.query('subject', 'age', '>', 2)
    assert len(projs.query('scan', 'task', '=', 'resting')) == 1
