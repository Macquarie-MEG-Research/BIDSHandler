import os.path as op
from os import listdir
import json
import xml.etree.ElementTree as ET
from .QueryMixin import QueryMixin

from .utils import (get_bids_params, realize_paths,
                    bids_params_are_subsets, splitall)

_SIDECAR_MAP = {'meg': 'meg',
                'fmap': 'phasediff',
                'func': 'bold'}


class Scan(QueryMixin):
    """Scan-level object.

    Parameters
    ----------
    fpath : str
        The path to the raw scan file.
    session : BIDSHandler.Session
        Parent Session object containing this Scan.
    scan_params : dict, optional
        A dictionary containing any number of other scan parameters specified
        by scans.tsv.
    """
    def __init__(self, fpath, session, **scan_params):
        super(Scan, self).__init__()
        self._path = splitall(fpath)[0]
        self._raw_file = '\\'.join(splitall(fpath)[1:])
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
        file_list.add(self.sidecar)
        file_list.update(realize_paths(self,
                                       list(self.associated_files.values())))
        return file_list

#region private methods

    def _assign_metadata(self):
        """Associate any files that are related to this raw file."""
        filename_data = get_bids_params(op.basename(self._raw_file))
        for fname in listdir(self.path):
            bids_params = get_bids_params(fname)
            part = bids_params.pop('part', None)
            if bids_params_are_subsets(filename_data, bids_params):
                if (bids_params['file'] == _SIDECAR_MAP.get(self._path,
                                                            None) and
                        bids_params['ext'] == '.json'):
                    self._sidecar = fname
                else:
                    # TODO: this will not work for .ds folders...
                    if not op.isdir(realize_paths(self, fname)):
                        if part is None:
                            self.associated_files[bids_params['file']] = fname
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
            filename_data = get_bids_params(op.basename(self._raw_file))
            for fname in self.session.inheritable_files:
                bids_params = get_bids_params(op.basename(fname))
                if bids_params_are_subsets(filename_data, bids_params):
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
        ET.Element
            Xml element containing subject information.
        """
        return ET.Element('Scan', attrib={'path': self.raw_file_relative})

    def _get_params(self):
        """Find the scan parameters from the file name."""
        filename_data = get_bids_params(op.basename(self._raw_file))
        self.task = filename_data.get('task', None)
        self.run = filename_data.get('run', None)
        self.acquisition = self.acq = filename_data.get('acq', None)
        self.proc = filename_data.get('proc', None)

    def _load_extras(self):
        """Load any extra files on a manufacturer-by-manufacturer basis."""
        if self.info.get('Manufacturer', None) == 'KIT/Yokogawa':
            # Need to load the marker files.
            # These will be in the same folder as the raw data.
            filename_data = get_bids_params(op.basename(self._raw_file))
            raw_folder = op.dirname(self._raw_file)
            for fname in listdir(op.join(self.path, raw_folder)):
                bids_params = get_bids_params(fname)
                if bids_params_are_subsets(filename_data, bids_params):
                    if bids_params['file'] == 'markers':
                        self.associated_files['markers'] = op.join(raw_folder,
                                                                   fname)

    def _load_info(self):
        """Read the sidecar.json and load the information into self.info"""
        if self._sidecar is not None:
            with open(self.sidecar, 'r') as sidecar:
                self.info = json.load(sidecar)

#region properties

    @property
    def bids_tree(self):
        """Parent BIDSTree object."""
        return self.project.bids_tree

    @property
    def channels_tsv(self):
        """Absolute path to the associated channels.tsv file."""
        channels_path = self.associated_files.get('channels', None)
        if channels_path is not None:
            return realize_paths(self, channels_path)
        return None

    @property
    def coordsystem_json(self):
        """Absolute path to the associated coordsystem.json file."""
        coordsystem_path = self.associated_files.get('coordsystem', None)
        if coordsystem_path is not None:
            return realize_paths(self, coordsystem_path)
        return None

    @property
    def events_tsv(self):
        """Absolute path to the associated events.tsv file."""
        events_path = self.associated_files.get('events', None)
        if events_path is not None:
            return realize_paths(self, events_path)
        return None

    @property
    def path(self):
        """Determine path location based on parent paths."""
        return op.join(self.session.path, self._path)

    @property
    def project(self):
        """Parent Project object."""
        return self.subject.project

    @property
    def raw_file(self):
        """Absolute path of associated raw file."""
        return realize_paths(self, self._raw_file)

    @property
    def raw_file_relative(self):
        """Relative path (to parent session) of associated raw file."""
        return op.join(self._path, self._raw_file)

    @property
    def sidecar(self):
        """Absolute path of associated sidecar file."""
        if self._sidecar is not None:
            return realize_paths(self, self._sidecar)
        return None

    @property
    def subject(self):
        """Parent Subject object."""
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
