from BIDSHandler.utils import get_bids_params, bids_params_are_subsets


def test_bids_params():
    # test splitting of file names into its parameters and test subset checking
    fname1 = 'sub-1_ses-1_task-resting_run-1_channels.tsv'
    split_fname1 = get_bids_params(fname1)
    assert split_fname1['sub'] == '1'
    assert split_fname1['task'] == 'resting'
    assert split_fname1['ext'] == '.tsv'
    assert split_fname1['file'] == 'channels'
    split_fname2 = get_bids_params('sub-1_ses-1_headshape.elp')
    assert bids_params_are_subsets(split_fname1, split_fname2)
    split_fname3 = get_bids_params('sub-1_ses-2_headshape.elp')
    assert not bids_params_are_subsets(split_fname1, split_fname3)
