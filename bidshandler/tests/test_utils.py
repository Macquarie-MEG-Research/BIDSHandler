import pytest
from datetime import datetime
import tempfile
import os.path as op

from bidshandler.utils import (_get_bids_params, _bids_params_are_subsets,
                               _compare, _compare_times, download_test_data,
                               _multi_replace)


def test_download_test_data():
    # test the downloading of test data
    with tempfile.TemporaryDirectory() as tmp:
        output_path = op.join(tmp, 'bidshandler_test_data')
        download_test_data(dst=output_path)
        with pytest.raises(FileExistsError):
            download_test_data(overwrite=False, dst=output_path)


def test_bids_params():
    # test splitting of file names into its parameters and test subset checking
    fname1 = 'sub-1_ses-1_task-resting_run-1_channels.tsv'
    split_fname1 = _get_bids_params(fname1)
    assert split_fname1['sub'] == '1'
    assert split_fname1['task'] == 'resting'
    assert split_fname1['ext'] == '.tsv'
    assert split_fname1['file'] == 'channels'
    # Check for when one set is a subset of the other.
    split_fname2 = _get_bids_params('sub-1_ses-1_headshape.elp')
    assert _bids_params_are_subsets(split_fname1, split_fname2)
    # Check for when one set is not a subset but the keys overlap.
    split_fname3 = _get_bids_params('sub-1_ses-2_headshape.elp')
    assert not _bids_params_are_subsets(split_fname1, split_fname3)
    # Check for when the two bids parameters are disjoint sets.
    split_fname4 = _get_bids_params('run-1_acq-test_meg.json')
    assert not _bids_params_are_subsets(split_fname3, split_fname4)


def test__compare():
    # test `_compare` and `_compare_times`
    assert _compare(1, '=', 1)
    assert _compare(1, '!=', '1')
    assert _compare(2, '>', 1)
    assert _compare(1, '<', 2)
    with pytest.raises(ValueError):
        _compare(1, 'a', 2)
    with pytest.raises(TypeError):
        _compare(1, '>=', 'a')

    ref_datetime = datetime.strptime('2018-10-26T11:22:33',
                                     '%Y-%m-%dT%H:%M:%S')
    ref_datetime2 = datetime.strptime('2018-10-27T11:22:33',
                                      '%Y-%m-%dT%H:%M:%S')
    ref_datetime3 = datetime.strptime('2018-10-26T22:22:33',
                                      '%Y-%m-%dT%H:%M:%S')
    ref_date = datetime.strptime('2018-10-26', "%Y-%m-%d").date()

    assert _compare_times(ref_datetime, '=', ref_date)
    assert _compare_times(ref_date, '=', ref_datetime3)
    assert _compare_times(ref_datetime2, '>', ref_datetime)
    with pytest.raises(TypeError):
        _compare_times(ref_date, '=', str)


def test__multi_replace():
    orig = 'this is a test'
    new = _multi_replace(orig, [], [])
    assert new == orig
    new = _multi_replace(orig, [' '], ['_'])
    assert new == 'this_is_a_test'
    new = _multi_replace(orig, [' ', 's', 'tezt'], ['_', 'z', 'thing'])
    assert new == 'thiz_iz_a_thing'
