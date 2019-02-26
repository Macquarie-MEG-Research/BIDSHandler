import os.path as op
import os
import json
import xml.etree.ElementTree as ET
from warnings import warn
import shutil

import pandas as pd

from .querymixin import QueryMixin
from .utils import (_get_bids_params, _realize_paths, _multi_replace,
                    _bids_params_are_subsets, _splitall, _fix_folderless,
                    _file_list)
from .bidserrors import NoScanError

_SIDECAR_MAP = {'meg': 'meg',
                'fmap': 'phasediff',
                'func': 'bold'}


class Scan(QueryMixin):
    """Scan-level object

    Parameters
    ----------
    fpath : str
        The path to the raw scan file.
    session : Instance of :class:`bidshandler.Session`
        Parent Session object containing this Scan.
    scan_params : dict, optional
        A dictionary containing any number of other scan parameters specified
        by scans.tsv.
    """
    def __init__(self, fpath, session, **scan_params):
        super(Scan, self).__init__()
        self._path = _splitall(fpath)[0]
        split_paths = _splitall(fpath)[1:]
        if len(split_paths) == 1:
            self._raw_file = split_paths
        elif len(split_paths) > 1:
            self._raw_file = op.join(split_paths[0], *split_paths[1:])
        self.acq_time = scan_params.pop('acq_time', None)
        self.scan_params = scan_params
        self.session = session
        self._get_params()
        self._sidecar = None

        self._queryable_types = ('scan',)

        self.associated_files = dict()
        self._assign_metadata()
        # Load information from the sidecar.
        self.info = dict()
        self._load_info()
        # Finally we do any manufacturer specific loading.
        self._load_extras()

#region public methods

    def contained_files(self):
        """Get the list of contained files.

        Returns
        -------
        file_list : list
            List with paths to all contained files relating to the BIDS
            structure.
        """
        file_list = set()
        if self.sidecar is not None:
            file_list.add(self.sidecar)
        file_list.update(_realize_paths(self,
                                        list(self.associated_files.values())))
        return file_list

    def delete(self):
        """Delete all the scan files."""
        for fname in self.contained_files():
            # make sure we only delete files that are in the same directory or
            # lower.
            if not fname.startswith('..'):
                # also make sure that there are no other scans in the same
                # session using the file
                used = False
                for scan in self.session.scans:
                    if scan != self:
                        if fname in scan.contained_files():
                            used = True
                            break
                if not used:
                    os.remove(fname)
        # remove the raw file
        os.remove(self.raw_file)

        # remove the scan information from the scans.tsv
        if self.session.scans_tsv is not None:
            df = pd.read_csv(self.session.scans_tsv, sep='\t')
            row_idx = df[df['filename'] == self.raw_file_relative].index.item()
            df = df.drop(row_idx)
            df.to_csv(self.session.scans_tsv, sep='\t', index=False,
                      na_rep='n/a', encoding='utf-8')
        # is the directory is empty remove it
        if len(list(_file_list(self.path))) == 0:
            shutil.rmtree(self.path)

        # remove the scan from the parent session
        self.session._scans.remove(self)
        # and delete self
        del self

#region private methods

    def _assign_metadata(self):
        """Associate any files that are related to this raw file."""
        filename_data = _get_bids_params(op.basename(self._raw_file))
        for fname in os.listdir(self.path):
            bids_params = _get_bids_params(fname)
            part = bids_params.pop('part', None)
            if _bids_params_are_subsets(filename_data, bids_params):
                if (bids_params['file'] == _SIDECAR_MAP.get(self._path,
                                                            None) and
                        bids_params['ext'] == '.json'):
                    self._sidecar = fname
                else:
                    # TODO: this will not work for .ds folders...
                    if not op.isdir(_realize_paths(self, fname)):
                        if part is None:
                            if fname == self._raw_file:
                                # Don't add the raw file name to the list.
                                continue
                            if bids_params['file'] in self.associated_files:
                                new_key = bids_params['file'] + \
                                    bids_params['ext']
                                self.associated_files[new_key] = fname
                            else:
                                self.associated_files[bids_params['file']] = \
                                    fname
                        else:
                            if part == '01':
                                # Assign the correct raw file name.
                                self._raw_file = fname
                            else:
                                # Give a unique key to avoid conflict if there
                                # are lots of parts for some reason...
                                key = str(bids_params['file']) + '_' + part
                                self.associated_files[key] = fname
        # If we have no sidecar file associated from the local folder, go over
        # the files that this folder inherit
        if self._sidecar is None:
            filename_data = _get_bids_params(op.basename(self._raw_file))
            for fname in self.session.inheritable_files:
                bids_params = _get_bids_params(op.basename(fname))
                if _bids_params_are_subsets(filename_data, bids_params):
                    if bids_params['ext'] == '.json':
                        if bids_params['file'] == _SIDECAR_MAP.get(self._path,
                                                                   None):
                            self._sidecar = op.relpath(fname, self.path)
                        else:
                            self.associated_files[bids_params['file']] = \
                                op.relpath(fname, self.path)
        # If there is still no sidecar file then it probably doesn't have one.

    def _generate_map(self):
        """Generate a map of the Subject.

        Returns
        -------
        :py:class:`xml.etree.ElementTree.Element`
            Xml element containing subject information.
        """
        return ET.Element('Scan', attrib={'path': self.raw_file_relative})

    def _get_params(self):
        """Find the scan parameters from the file name."""
        filename_data = _get_bids_params(op.basename(self._raw_file))
        self.task = filename_data.get('task', None)
        self.run = filename_data.get('run', None)
        self.acquisition = self.acq = filename_data.get('acq', None)
        self.proc = filename_data.get('proc', None)

    def _load_extras(self):
        """Load any extra files on a manufacturer-by-manufacturer basis."""
        if self.info.get('Manufacturer', None) == 'KIT/Yokogawa':
            # Need to load the marker files.
            # These will be in the same folder as the raw data.
            filename_data = _get_bids_params(op.basename(self._raw_file))
            raw_folder = op.dirname(self._raw_file)
            for fname in os.listdir(op.join(self.path, raw_folder)):
                bids_params = _get_bids_params(fname)
                if _bids_params_are_subsets(filename_data, bids_params):
                    if bids_params['file'] == 'markers':
                        self.associated_files['markers'] = op.join(raw_folder,
                                                                   fname)

    def _load_info(self):
        """Read the sidecar.json and load the information into self.info"""
        if self._sidecar is not None:
            with open(self.sidecar, 'r') as sidecar:
                self.info = json.load(sidecar)

    def _rename(self, subj_id, sess_id):
        """Rename all the files contained by the scan.

        Parameters
        ----------
        subj_id : str
            Raw subject ID value. Ie. *without* `sub-`.
        sess_id : str
            Raw session ID value. Ie. *without* `ses-`.
        """
        # TODO: handle moving of anat data
        old_subj_id = self.subject.ID
        new_subj_id = 'sub-{0}'.format(subj_id)
        old_sess_id = self.session.ID
        new_sess_id = 'ses-{0}'.format(sess_id)
        # rename all the contained files
        for fname in self.contained_files():
            # make sure we only rename files that are in the same directory or
            # lower.
            if not fname.startswith('..'):
                new_fname = _fix_folderless(self.session, fname, old_sess_id,
                                            old_subj_id)
                new_fname = _multi_replace(new_fname,
                                           [old_subj_id, old_sess_id],
                                           [new_subj_id, new_sess_id])
                if not op.exists(op.dirname(new_fname)):
                    os.makedirs(op.dirname(new_fname))
                os.rename(fname, new_fname)
        # rename the raw file
        old_fname = self.raw_file
        new_fname = _fix_folderless(self.session, old_fname, old_sess_id,
                                    old_subj_id)
        new_fname = _multi_replace(new_fname, [old_subj_id, old_sess_id],
                                   [new_subj_id, new_sess_id])
        if not op.exists(op.dirname(new_fname)):
            os.makedirs(op.dirname(new_fname))
        os.rename(old_fname, new_fname)
        self._raw_file = _fix_folderless(self.session, self._raw_file,
                                         old_sess_id, old_subj_id)
        self._raw_file = _multi_replace(self._raw_file,
                                        [old_subj_id, old_sess_id],
                                        [new_subj_id, new_sess_id])

        # rename all the internal file names
        if self._sidecar is not None:
            self._sidecar = _fix_folderless(self.session, self._sidecar,
                                            old_sess_id, old_subj_id)
            self._sidecar = _multi_replace(self._sidecar,
                                           [old_subj_id, old_sess_id],
                                           [new_subj_id, new_sess_id])
        for key, value in self.associated_files.items():
            value = _fix_folderless(self.session, value, old_sess_id,
                                    old_subj_id)
            self.associated_files[key] = _multi_replace(
                value, [old_subj_id, old_sess_id], [new_subj_id, new_sess_id])

#region properties

    @property
    def bids_tree(self):
        """Parent :class:`bidshandler.BIDSTree` object."""
        return self.project.bids_tree

    @property
    def channels_tsv(self):
        """Path to the associated channels.tsv file if there is one."""
        _path = None
        channels_path = self.associated_files.get('channels')
        if channels_path is not None:
            _path = _realize_paths(self, channels_path)
        return _path

    @property
    def coordsystem_json(self):
        """Path to the associated coordsystem.json file if there is one."""
        _path = None
        coordsystem_path = self.associated_files.get('coordsystem')
        if coordsystem_path is not None:
            _path = _realize_paths(self, coordsystem_path)
        return _path

    @property
    def emptyroom(self):
        """Associated emptyroom Scan.

        Returns
        -------
        :class:`bidshandler.Scan`
            Associated emptyroom Scan object.

        Note
        ----
        Only for MEG scans.
        """
        _path = None
        if self.scan_type == 'meg':
            emptyroom = self.info.get('AssociatedEmptyRoom')
            if emptyroom is not None:
                fname = op.basename(emptyroom)
                bids_params = _get_bids_params(fname)
                try:
                    _path = self.project.subject(
                        bids_params['sub']).session(
                            bids_params['ses']).scan(
                                task=bids_params.get('task'),
                                acq=bids_params.get('acq'),
                                run=bids_params.get('run'))
                except (KeyError, NoScanError):
                    msg = 'Associated empty room file for {0} cannot be found'
                    warn(msg.format(str(self)))
                    _path = None
        return _path

    @property
    def events_tsv(self):
        """Absolute path to the associated events.tsv file."""
        _path = None
        events_path = self.associated_files.get('events')
        if events_path is not None:
            _path = _realize_paths(self, events_path)
        return _path

    @property
    def path(self):
        """Path of folder containing Scan."""
        return op.join(self.session.path, self._path)

    @property
    def project(self):
        """Parent :class:`bidshandler.Project` object."""
        return self.subject.project

    @property
    def raw_file(self):
        """Path of associated raw file."""
        return _realize_paths(self, self._raw_file)

    @property
    def raw_file_relative(self):
        """Path of associated raw file relative to parent Session."""
        return op.join(self._path, self._raw_file)

    @property
    def scan_type(self):
        """Type of Scan.

        This will be the name of the folder the Scan resides in.
        Eg. `meg` for MEG data, `func` for fMRI data.
        """
        return self._path

    @property
    def sidecar(self):
        """Path of associated sidecar file if there is one."""
        _path = None
        if self._sidecar is not None:
            _path = _realize_paths(self, self._sidecar)
        return _path

    @property
    def subject(self):
        """Parent :class:`bidshandler.Subject` object."""
        return self.session.subject

#region class methods

    def __eq__(self, other):
        """Implements self == other

        Returns True if each instance has the same set of parameters
        """
        if not isinstance(other, Scan):
            raise TypeError("Can only compare two Scan objects.")
        return ((self.acq == other.acq) &
                (self.task == other.task) &
                (self.run == other.run) &
                (self.proc == other.proc) &
                (self.session._id == other.session._id) &
                (self.subject._id == other.subject._id) &
                (self.project._id == other.project._id))

    def __repr__(self):
        return '<Scan, @ {0}>'.format(self.raw_file)

    def __str__(self):
        return self.raw_file_relative
