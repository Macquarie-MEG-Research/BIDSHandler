import os.path as op


#region values

# MEG Manufacturers
MEG_MAN1 = 'KIT/Yokogawa'
MEG_MAN2 = 'Elekta'
MEG_MAN3 = '4D Magnes'
MEG_MAN4 = 'CTF'

# EEG Manufacturers
EEG_MAN1 = 'BrainProducts'
EEG_MAN2 = 'Biosemi'

#region lookups

EEG_MANUFACTURERS = {'.vhdr': EEG_MAN1, '.eeg': EEG_MAN1, '.bdf': EEG_MAN2}

MEG_MANUFACTURERS = {'.sqd': MEG_MAN1, '.con': MEG_MAN1, '.fif': MEG_MAN2,
                     '.pdf': MEG_MAN3, '.ds': MEG_MAN4, '.meg4': MEG_MAN4}

RAW_FILETYPES = ('.nii', '.bdf', '.con', '.sqd')

SIDECAR_MAP = {'meg': 'meg',
               'fmap': 'phasediff',
               'func': 'bold'}


def test_path():
    """ Path where all the test data is located """
    return op.join(op.expanduser('~'), 'bidshandler_test_data')
