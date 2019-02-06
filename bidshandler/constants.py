import os.path as op


def test_path():
    """ Path where all the test data is located """
    return op.join(op.expanduser('~'), 'bidshandler_test_data')
