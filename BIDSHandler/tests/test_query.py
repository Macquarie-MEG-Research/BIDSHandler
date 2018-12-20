# test the query functionality

import pytest

from BIDSHandler import BIDSFolder

TESTPATH1 = 'data/BIDSTEST1'


def test_query():
    folder = BIDSFolder(TESTPATH1)

    # query some subject information
    assert len(folder.query('subject', 'age', '=', 4)) == 1
    assert len(folder.query('subject', 'age', '>', 2)) == 2
    assert len(folder.query('subject', 'age', '>=', 2)) == 3
    assert len(folder.query('subject', 'sex', '=', 'M')) == 1
    assert len(folder.query('subject', 'sex', '!=', 'M')) == 2
    assert len(folder.query('subject', 'group', '=', 'autistic')) == 2
    with pytest.raises(ValueError, match="subject data"):
        folder.query('project', 'age', '=', '4')
    with pytest.raises(ValueError, match="subject data"):
        folder.query('session', 'sex', '=', 'M')
    with pytest.raises(ValueError, match="subject data"):
        folder.query('scan', 'group', '=', 'autistic')

    # query some tasks
    assert len(folder.query('scan', 'task', '=', 'resting')) == 2
    # ask if any of the subjects has *any* tasks that aren't 'resting'
    assert (folder.query('subject', 'task', '!=', 'resting')[0] ==
            folder.project('test1').subject('1'))
    # ask if any of the subjects have not got a task called 'resting'
    assert (folder.query('subject', 'task', '!!=', 'resting')[0] ==
            folder.project('test1').subject('2'))

    # query the recording date
    ref_datetime = '2018-10-26T11:32:33'
    ref_date = '2018-10-26'
    assert len(folder.query('scan', 'rec_date', '=', ref_datetime)) == 1
    assert len(folder.query('scan', 'rec_date', '<=', ref_datetime)) == 4
    assert len(folder.query('scan', 'rec_date', '>', ref_datetime)) == 1
    assert len(folder.query('scan', 'rec_date', '=', ref_date)) == 5

    # query some data in the sidecar.json:
    assert len(folder.query('project', 'PowerLineFrequency', '=', 50)) == 2
    assert len(folder.query('subject', 'MiscChannelCount', '=', 93)) == 3
    assert len(folder.query('session', 'TaskName', '=', 'resting')) == 2
    assert len(folder.query('scan', 'RecordingDuration', '>=', 5)) == 5
