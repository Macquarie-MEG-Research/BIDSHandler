import os
import os.path as op
from collections import OrderedDict

import pandas as pd

from .utils import get_bids_params, copyfiles, realize_paths, combine_tsv
from .BIDSErrors import MappingError, NoScanError, AssociationError
from .Scan import Scan


class Session():
    """Object to describe a session level folder.

    Parameters
    ----------
    id_ : int | str
        The session id.
        The id by itself can be accessed by `._id`, and the id with the `ses`
        prefix can be accessed by the more common `.ID`.
    subject : Instance of Subject
        Parent Subject object.
    initialize : bool
        Whether or not to load the session folder's data.
        Defaults to True.
    """
    def __init__(self, id_, subject, initialize=True):
        self._id = id_
        self.subject = subject
        self._scans_tsv = None
        self._scans = []
        self.recording_types = []

        if initialize:
            self.determine_content()
            self._check()

#region public methods

    def add(self, other, copier=copyfiles):
        """Add another Scan to this object.

        Parameters
        ----------
        other : Instance of Session or Scan
            Scan object to be added to this session.
            The scan must previously exist in the same project, subject and
            session as this current session.
        copier : function
            A function to facilitate the copying of any applicable data.
            This function must have the call signature
            `function(src_files: list, dst: string)`
            Where src_files is the list of files to be moved and dst is the
            destination folder.
            This will default to using utils.copyfiles which simply implements
            shutil.copy.
        """
        if isinstance(other, Session):
            if self._id == other._id:
                for scan in other.scans:
                    self.add(scan, copier)
            else:
                raise ValueError("Added session must have same ID.")
        elif isinstance(other, Scan):
            # TODO-LT: handle other modalities
            # we need to make sure that the scan is of the same person/session:
            if (self._id == other.session._id and
                    self.subject._id == other.subject._id and
                    self.project._id == other.project._id):
                # Handle merging the scans.tsv file
                if other in self:
                    # we don't want to add it if it is already in this session
                    # TODO: add overwrite argument to allow it to still be
                    # added.
                    return
                other_scan_df = pd.DataFrame(
                    OrderedDict([
                        ('filename', [other.raw_file_relative]),
                        ('acq_time', [other.acq_time])]),
                    columns=['filename', 'acq_time'])
                # combine the new data into the original tsv
                combine_tsv(self.scans_tsv, other_scan_df, 'filename')

                file_list = (list(other.associated_files.values()) +
                             [other._sidecar])
                if other.info['Manufacturer'] != 'Elekta':
                    # I think I only elekta data will have it already picked up
                    file_list.append(other._raw_file)
                # copy the files over
                fl_left = realize_paths(other, file_list)
                fl_right = []
                for fpath in file_list:
                    fl_right.append(op.join(self.path, other._path, fpath))
                copier(fl_left, fl_right)
                # add the scan object to our scans list
                scan = Scan(other.raw_file_relative, other.acq_time, self)
                self._scans.append(scan)
            else:
                raise AssociationError("scan", "project, subject and session")
        else:
            raise TypeError("Cannot add a {0} object to a Subject".format(
                type(other).__name__))

    def contained_files(self):
        """Get the list of contained files."""
        file_list = set()
        file_list.add(realize_paths(self, self._scans_tsv))
        for scan in self.scans:
            file_list.update(scan.contained_files())
        return file_list

    def create_empty_scan_tsv(self):
        """Create an empty scans.tsv file for this session."""
        self._scans_tsv = '{0}_{1}_scans.tsv'.format(self.subject.ID, self.ID)
        full_path = realize_paths(self, self._scans_tsv)
        if not op.exists(full_path):
            df = pd.DataFrame(OrderedDict([('filename', []),
                                           ('acq_time', [])]),
                              columns=['filename', 'acq_time'])
            df.to_csv(full_path, sep='\t', index=False, na_rep='n/a',
                      encoding='utf-8')

    # TODO: Rename?
    def determine_content(self):
        """Parse the session folder to find what recordings are included."""
        for fname in os.listdir(self.path):
            full_path = op.join(self.path, fname)
            # Each sub-directory is considered a separate type of recording.
            if op.isdir(full_path):
                self.recording_types.append(fname)
            # The only other non-folder should be the scans tsv.
            else:
                filename_data = get_bids_params(fname)
                if filename_data.get('file', None) == 'scans':
                    # Store the path and extract the paths of the scans.
                    self._scans_tsv = fname
                    scans = pd.read_csv(realize_paths(self, self._scans_tsv),
                                        sep='\t')
                    for i in range(len(scans)):
                        row = scans.iloc[i]
                        self._scans.append(
                            Scan(row['filename'], row['acq_time'], self))

    def scan(self, task=None, acq=None, run=None):
        # TODO: allow this to return a list if mutliple scans match
        # consider None a wildcard.
        for scan in self.scans:
            if (scan.task == task and scan.acq == acq and scan.run == run):
                return scan
        raise NoScanError

#region private methods

    def _check(self):
        if len(self._scans) == 0:
            raise MappingError

    @staticmethod
    def _clone_into_subject(subject, other):
        """Create a copy of the Session with a new parent Subject.

        Parameters
        ----------
        subjecty : Instance of Subject
            New parent Subject.
        other : instance of Session
            Original Session instance to clone.
        """
        os.makedirs(realize_paths(subject, other.ID), exist_ok=True)
        # Create a new empty session object.
        new_session = Session(other._id, subject, initialize=False)
        new_session.create_empty_scan_tsv()
        return new_session

#region properties

    @property
    def bids_folder(self):
        """Parent BIDSFolder object."""
        return self.project.bids_folder

    @property
    def ID(self):
        """ID with 'ses' prefix."""
        return 'ses-{0}'.format(self._id)

    @property
    def path(self):
        """Determine path location based on parent paths."""
        return op.join(self.subject.path, self.ID)

    @property
    def project(self):
        """Parent Project object."""
        return self.subject.project

    @property
    def scans(self):
        """List of contained Scans."""
        return self._scans

    @property
    def scans_tsv(self):
        """Absolute path of associated scans.tsv file."""
        return realize_paths(self, self._scans_tsv)

#region class methods

    def __contains__(self, other):
        """Determine whether the Session object contains a scan.

        Parameters
        ----------
        other : Instance of Scan
            Scan object to test whether it is contained in this Session.
        """
        for scan in self._scans:
            if scan == other:
                return True
        return False

    def __iter__(self):
        return iter(self._scans)

    def __repr__(self):
        output = []
        output.append('ID: {0}'.format(self.ID))
        output.append('Number of scans: {0}'.format(len(self.scans)))
        return '\n'.join(output)
