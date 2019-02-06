import pytest
from datetime import datetime

from bidshandler.utils import (_get_bids_params, _bids_params_are_subsets,
                               _compare, _compare_times, download_test_data)


def test_download_test_data():
    # test the downloading of test data
    download_test_data()
    with pytest.raises(FileExistsError):
        download_test_data(overwrite=False)


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
