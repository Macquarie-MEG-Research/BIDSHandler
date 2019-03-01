import os.path as op
import os
import shutil
from datetime import datetime, date
import zipfile
import urllib.request
import tempfile

import pandas as pd

from .constants import test_path


#region public functions

def download_test_data(overwrite=True, dst=None):
    """ Download the BIDS-standard test data to the test folder.

    Parameters
    ----------
    overwrite : bool
        Whether to overwrite previous test data.
        If True this will remove the previous test_data folder and write a
        new one.
    dst : str or path-like object
        Specific path to download test data to. This is only for debugging/
        testing purposes.
    """
    if dst is None:
        test_data_root = test_path()
    else:
        test_data_root = dst

    if op.exists(test_data_root):
        if overwrite:
            shutil.rmtree(test_data_root)
        else:
            raise FileExistsError

    bids_test_data_url = 'https://github.com/bids-standard/bids-examples/archive/master.zip'  # noqa
    bh_test_data_url = 'https://github.com/Macquarie-MEG-Research/BIDSHandler/archive/test_data.zip'  # noqa
    with tempfile.TemporaryDirectory() as tmp:
        # download all the bids-standard test data and move
        print('Downloading bids-standard data')
        zip_dst = op.join(tmp, 'master.zip')
        urllib.request.urlretrieve(bids_test_data_url, zip_dst)
        zf = zipfile.ZipFile(zip_dst)
        print('Extracting bids-standard data')
        zf.extractall(tmp)
        zf.close()
        shutil.copytree(op.join(tmp, 'bids-examples-master'),
                        op.join(test_data_root, 'bids-examples'))
        # download the bidshandler test data also
        print('Downloading BIDSHandler data')
        zip_dst = op.join(tmp, 'test_data.zip')
        urllib.request.urlretrieve(bh_test_data_url, zip_dst)
        zf = zipfile.ZipFile(zip_dst)
        print('Extracting BIDSHandler data')
        zf.extractall(tmp)
        zf.close()
        data_folder = op.join(tmp, 'BIDSHandler-test_data', 'data')
        for fname in os.listdir(data_folder):
            shutil.copytree(op.join(data_folder, fname),
                            op.join(test_data_root, fname))


#region private functions


def _file_list(folder):
    """ List of all the files contained recursively within a directory """
    for root, _, files in os.walk(folder):
        for _file in files:
            yield op.join(root, _file)


def _bids_params_are_subsets(params1, params2):
    """
    Equivalent to asking if params1 ⊇ params2.
    Ie. returns true if set(params2) is a subset of set(params1).
    """
    param1_keys = set(params1.keys())
    param2_keys = set(params2.keys())
    for key in ['file', 'ext']:
        param1_keys = param1_keys - {key}
        param2_keys = param2_keys - {key}
    if param1_keys >= param2_keys:
        for key in param2_keys:
            if not params2[key] == params1[key]:
                return False
        return True
    return False


def _combine_tsv(tsv, df, drop_column=None):
    """Merge a df into a tsv file"""
    orig_df = pd.read_csv(tsv, sep='\t')
    orig_df = orig_df.append(df, sort=False)
    if drop_column is not None:
        orig_df.drop_duplicates(subset=drop_column, keep='last', inplace=True)
    orig_df.to_csv(tsv, sep='\t', index=False, na_rep='n/a', encoding='utf-8')


def _compare(val1, conditional, val2):
    """Compare the two values using the specified conditional
    ie. returns val1 (conditional) val2
    """
    if conditional == '<':
        return val1 < val2
    elif conditional in ('<=', '=<'):
        return val1 <= val2
    elif conditional in ('=', '=='):
        return val1 == val2
    elif conditional in ('=>', '>='):
        return val1 >= val2
    elif conditional == '>':
        return val1 > val2
    elif conditional in ('!=', '!!='):
        # Generally a `!!=` conditional will be caught by calling code to
        # handle it correctly, however sometimes it makes sense to use it in
        # the same way as the `!=` conditional.
        return val1 != val2
    else:
        raise ValueError("Invalid conditional {0} entered".format(conditional))


def _compare_times(time1, conditional, time2):
    """
    Compares two datetime objects to determine if they are the same.

    This differs to normal comparison as it allows for comparison between
    datetime.date objects and datetime.datetime objects.
    Equality can thus be determine in such a way that it can be determined if
    one specfic time on a day is on that day (by equating a date object to a
    datetime object).
    """
    if type(time1) == type(time2):
        # Just do a normal compare.
        return _compare(time1, conditional, time2)
    else:
        if isinstance(time1, date) and isinstance(time2, datetime):
            return _compare(time1, conditional, time2.date())
        elif isinstance(time1, datetime) and isinstance(time2, date):
            return _compare(time1.date(), conditional, time2)
        else:
            raise TypeError


def _copyfiles(src_files, dst_files):
    """
    Copy a list of files to a list of destinations.

    Parameters
    ----------
    src_files : list of str's
        List of source paths.
    dst_files : list of str's
        List of destination paths.

    Note:
    -----
    There is a one-to-one correlation between the src_files and dst_files
    lists. Ie. src_files[i] will be copied to dst_files[i].
    """
    assert len(src_files) == len(dst_files)
    for fnum in range(len(src_files)):
        if not op.exists(op.dirname(dst_files[fnum])):
            os.makedirs(op.dirname(dst_files[fnum]), exist_ok=True)
        try:
            shutil.copy(src_files[fnum], dst_files[fnum])
        except shutil.SameFileError:
            # For now just skip files that are the same.
            print('same file!!')


def _fix_folderless(session, fname, old_sess_id, old_subj_id):
    # TODO: join this into _multi_replace?
    if session.has_no_folder:
        # replace all the sub-XX with sub-XX_ses-YY
        fname = fname.replace(old_subj_id, old_subj_id + '_' + old_sess_id)
        # then replace the sub-XX_ses-YY in the path to sub-XX/ses-YY
        fname = fname.replace(old_subj_id + '_' + old_sess_id + op.sep,
                              op.join(old_subj_id, old_sess_id) + op.sep)
    return fname


def _get_bids_params(fname):
    filename, ext = op.splitext(fname)
    f = filename.split('_')
    data = {'ext': ext}
    for i in f:
        if '-' in i:
            data[i.split('-')[0]] = i.split('-')[1]
        else:
            data['file'] = i
    return data


def _multi_replace(str_in, old, new):
    """Replace all instances of all strings in `old` with the strings in `new`

    Parameters
    ----------
    str_in : str
        Original string.
    old : list(str)
        List of strings to be replaced.
    new : list(str)
        List of string to replace with.

    Returns
    -------
    str_out : str
        String with values replaced.
    """
    if ((not isinstance(old, list)) or (not isinstance(new, list)) or
            len(old) != len(new)):
        raise ValueError
    str_out = str_in
    for i in range(len(old)):
        str_out = str_out.replace(old[i], new[i])
    return str_out


def _prettyprint_xml(xml_str):
    """Take a flat string representation of xml data and pretty print it."""
    curr_indent = 0
    pointer = 0
    return_data = []
    while True:
        start = xml_str.find('<', pointer)
        end = xml_str.find('>', pointer)
        try:
            # Determine how the indentation should change.
            if xml_str[end - 1] == '/' and xml_str[end + 2] != '/':
                curr_indent = curr_indent
            elif xml_str[end - 1] == '/' and xml_str[end + 2] == '/':
                curr_indent -= 1
            elif xml_str[end - 1] != '/' and xml_str[end + 2] == '/':
                curr_indent -= 1
            elif xml_str[end - 1] != '/' and xml_str[end + 2] != '/':
                ret_str = xml_str[start: end + 1]
                if ' ' not in ret_str and '=' not in ret_str:
                    curr_indent = curr_indent
                else:
                    curr_indent += 1
            return_data.append(xml_str[start: end + 1])
            return_data.append('\n')
            return_data.append(curr_indent * '\t')
            pointer = end + 1
        except IndexError:
            return_data.append(xml_str[start: end + 1])
            break

    return ''.join(return_data)


# This could possibly be a method for the classes? If they become subclassed
# it would only need to be defined for the base class.
# this could also be a decorator taking the instance of the class as an arg
def _realize_paths(obj, rel_paths):
    """Returns the actual path to a file.

    Parameters
    ----------
    obj : Instance of Project, Subject, Session or Scan
        The object the path will be found relative to.
    rel_path : str
        Relative path from an object

    """
    if isinstance(rel_paths, (list, set)):
        ret_paths = []
        for fpath in rel_paths:
            ret_paths.append(op.normpath(op.join(obj.path, fpath)))
        return ret_paths
    return op.normpath(op.join(obj.path, rel_paths))


def _reformat_fname(fname):
    """Change all the path separators in a file path to `/`"""
    return fname.replace(os.sep, '/')


def _splitall(fpath):
    # credit: Trent Mick:
    # https://www.oreilly.com/library/view/python-cookbook/0596001673/ch04s16.html
    allparts = []
    # first, need to fix the path name to be split-able on the current OS:
    # temp fix while fix is addressed in mne-bids:
    if '\\' in fpath:
        fpath = fpath.replace('\\', os.sep)
    elif '/' in fpath:
        fpath = fpath.replace('/', os.sep)
    while 1:
        parts = op.split(fpath)
        if parts[0] == fpath:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == fpath:  # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            fpath = parts[0]
            allparts.insert(0, parts[1])
    return allparts
