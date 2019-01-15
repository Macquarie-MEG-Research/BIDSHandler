import os.path as op
from os import listdir
import json
import xml.etree.ElementTree as ET

from .BIDSErrors import MappingError
from .utils import (get_bids_params, realize_paths,
                    bids_params_are_subsets, splitall)


class Scan():
    def __init__(self, fpath, acq_time, session):
        self._path = splitall(fpath)[0]
        self._raw_file = '\\'.join(splitall(fpath)[1:])
        self.acq_time = acq_time
        self.session = session
        self._get_params()
        self._sidecar = None
        self.associated_files = dict()
        self._assign_metadata()
        # Load information from the sidecar.
        self.info = dict()
        self._load_info()
        # Finally we do any manufacturer specific loading.
        self._load_extras()

#region public methods

    def contained_files(self):
        """Get the list of contained files."""
        file_list = set()
        file_list.add(self.sidecar)
        file_list.update(realize_paths(self,
                                       list(self.associated_files.values())))
        return file_list

#region private methods

    def _assign_metadata(self):
        """Scan folder for associated metadata files."""
        filename_data = get_bids_params(op.basename(self._raw_file))
        for fname in listdir(self.path):
            bids_params = get_bids_params(fname)
            part = bids_params.pop('part', None)
            if bids_params_are_subsets(filename_data, bids_params):
                if (bids_params['file'] == self._path and
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

        self._check()

    def _check(self):
        if self._sidecar is None:
            raise MappingError

    def _generate_map(self):
        """Generate a map of the Scan."""
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
        if self.info['Manufacturer'] == 'KIT/Yokogawa':
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
        with open(self.sidecar, 'r') as sidecar:
            self.info = json.load(sidecar)

#region properties

    @property
    def channels_tsv(self):
        """Absolute path to the associated channels.tsv file."""
        channels_path = self.associated_files.get('channels', None)
        if channels_path is not None:
            return realize_paths(self, channels_path)
        else:
            raise FileNotFoundError

    @property
    def coordsystem_json(self):
        """Absolute path to the associated coordsystem.json file."""
        coordsystem_path = self.associated_files.get('coordsystem', None)
        if coordsystem_path is not None:
            return realize_paths(self, coordsystem_path)
        else:
            raise FileNotFoundError

    @property
    def events_tsv(self):
        """Absolute path to the associated events.tsv file."""
        events_path = self.associated_files.get('events', None)
        if events_path is not None:
            return realize_paths(self, events_path)
        else:
            raise FileNotFoundError

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
        return realize_paths(self, self._sidecar)

    @property
    def subject(self):
        """Parent Subject object."""
        return self.session.subject

#region class methods

    def __eq__(self, other):
        return ((self.acq == other.acq) &
                (self.task == other.task) &
                (self.run == other.run) &
                (self.session._id == other.session._id) &
                (self.subject._id == other.subject._id) &
                (self.project._id == other.project._id))

    def __repr__(self):
        return '<Scan, @ {0}>'.format(self.raw_file)

    def __str__(self):
        return self.raw_file_relative
