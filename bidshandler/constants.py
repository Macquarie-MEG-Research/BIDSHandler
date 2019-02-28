import os.path as op

_RAW_FILETYPES = ('.nii', '.bdf', '.con', '.sqd')

_SIDECAR_MAP = {'meg': 'meg',
                'fmap': 'phasediff',
                'func': 'bold'}


def test_path():
    """ Path where all the test data is located """
    return op.join(op.expanduser('~'), 'bidshandler_test_data')
