import os
import os.path as op
from collections import OrderedDict

import xml.etree.ElementTree as ET

import pandas as pd

from .utils import get_bids_params, copyfiles, realize_paths, combine_tsv
from .BIDSErrors import MappingError, NoScanError, AssociationError
from .Scan import Scan
from .QueryMixin import QueryMixin


_RAW_FILETYPES = ('.nii', '.bdf', '.con', '.sqd')   # TODO: add more...


class Session(QueryMixin):
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
    no_folder : bool
        Whether or not the session is contained within a `ses-XX` folder.
        For experiments with multiple sessions each folder will correspond to
        a Session object, however if there is only a single session this can
        be omitted and the Subject folder is in fact the Session folder.
    """
    def __init__(self, id_, subject, initialize=True, no_folder=False):
        super(Session, self).__init__()
        self._id = id_
        self.subject = subject
        self._scans_tsv = None
        self._scans = []
        self.recording_types = []

        self._queryable_types = ('session', 'scan')

        self.has_no_folder = no_folder

        if initialize:
            self._add_scans()
            self._check()

#region public methods

    def add(self, other, copier=copyfiles):
        """Add another Scan or Session to this object.

        Parameters
        ----------
        other : Instance of Scan or Session
            Object to be added to this Session.
            The added object must already exist in the same context as this
            object.
        copier : function
            A function to facilitate the copying of any applicable data.
            This function must have the call signature
            `function(src_files: list, dst_files: list)`
            Where src_files is the list of files to be moved and dst_files is
            the list of corresponding destinations.
            This will default to using utils.copyfiles which simply implements
            shutil.copy and creates any directories that do not already exist.
        """
        if isinstance(other, Session):
            if self._id == other._id:
                for scan in other.scans:
                    self.add(scan, copier)
            else:
                raise ValueError("Added session must have same ID.")
        elif isinstance(other, Scan):
            # TODO-LT: handle other modalities
            # We need to make sure that the scan is of the same person/session:
            if (self._id == other.session._id and
                    self.subject._id == other.subject._id and
                    self.project._id == other.project._id):
                # Handle merging the scans.tsv file.
                if other in self:
                    # We don't want to add it if it is already in this session.
                    # TODO: add overwrite argument to allow it to still be
                    # added.
                    return
                other_scan_df = pd.DataFrame(
                    OrderedDict([
                        ('filename', [other.raw_file_relative]),
                        ('acq_time', [other.acq_time])]),
                    columns=['filename', 'acq_time'])
                # Combine the new data into the original tsv.
                combine_tsv(self.scans_tsv, other_scan_df, 'filename')

                # Assign as a set to avoid any potential doubling of the raw
                # file path.
                files = set(other.associated_files.values())
                files.add(other._sidecar)
                files.add(other._raw_file)
                # Copy the files over.
                fl_left = realize_paths(other, files)
                fl_right = []
                for fpath in files:
                    fl_right.append(op.join(self.path, other._path, fpath))
                copier(fl_left, fl_right)
                # Add the scan object to our scans list.
                scan = Scan(other.raw_file_relative, self,
                            acq_time=other.acq_time)
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

    def scan(self, task=None, acq=None, run=None):
        # TODO: Allow this to return a list if mutliple scans match.
        # Consider None a wildcard.
        for scan in self.scans:
            if (scan.task == task and scan.acq == acq and scan.run == run):
                return scan
        raise NoScanError

#region private methods

    def _add_scans(self):
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
                    column_names = set(scans.columns.values)
                    if 'filename' not in column_names:
                        raise MappingError(
                            "{0} contains no 'filename' column".format(
                                self.scans_tsv))
                    column_names.remove('filename')
                    for i in range(len(scans)):
                        row = scans.iloc[i]
                        fname = row.pop('filename')
                        self._scans.append(
                            Scan(fname, self, **dict(row)))
        # if we haven't found a scans.tsv file then we need to add all the
        # scans in a different way.
        if self._scans_tsv is None:
            # for now do just MRI stuff which is any .nii.gz file I think?
            #TODO: have a switch for each folder name?
            for rec_type in self.recording_types:
                if rec_type not in ('anat', 'dwi'):
                    rec_path = realize_paths(self, rec_type)
                    if rec_type == 'fmap':
                        # fieldmap sequence
                        # The files with `file` = `magnitude1` are not raw
                        # scans.
                        filename_data = get_bids_params(fname)
                        if ((filename_data['file'] not in ('magnitude1',
                                                           'magnitude2')) and
                                'nii' in fname):
                            self._scans.append(
                                Scan(op.join(rec_type, fname), self))

                    for fname in os.listdir(rec_path):
                        for ext in _RAW_FILETYPES:
                            if ext in fname:
                                self._scans.append(
                                    Scan(op.join(rec_type, fname), self))

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
        new_session._create_empty_scan_tsv()
        return new_session

    def _create_empty_scan_tsv(self):
        """Create an empty scans.tsv file for this session."""
        self._scans_tsv = '{0}_{1}_scans.tsv'.format(self.subject.ID, self.ID)
        full_path = realize_paths(self, self._scans_tsv)
        if not op.exists(full_path):
            df = pd.DataFrame(OrderedDict([('filename', [])]),
                              columns=['filename'])
            df.to_csv(full_path, sep='\t', index=False, na_rep='n/a',
                      encoding='utf-8')

    def _generate_map(self):
        """Generate a map of the Session."""
        root = ET.Element('Session', attrib={'ID': str(self._id)})
        for scan in self.scans:
            root.append(scan._generate_map())
        return root

#region properties

    @property
    def bids_tree(self):
        """Parent BIDSTree object."""
        return self.project.bids_tree

    @property
    def ID(self):
        """ID with 'ses' prefix."""
        return 'ses-{0}'.format(self._id)

    @property
    def inheritable_files(self):
        files = self.subject.inheritable_files
        for fname in os.listdir(self.path):
            abs_path = realize_paths(self, fname)
            if op.isfile(abs_path):
                files.append(abs_path)
        return files

    @property
    def path(self):
        """Determine path location based on parent paths."""
        if self.has_no_folder:
            return self.subject.path
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
            Object to test whether it is contained in this Session.
        """
        if isinstance(other, Scan):
            for scan in self._scans:
                if scan == other:
                    return True
            return False
        raise TypeError("Can only determine if a Scan is contained.")

    def __iter__(self):
        return iter(self._scans)

    def __repr__(self):
        return '<Session, ID: {0}, {1} scan{2}, @ {3}>'.format(
            self.ID,
            len(self.scans),
            ('s' if len(self.scans) > 1 else ''),
            self.path)

    def __str__(self):
        output = []
        output.append('ID: {0}'.format(self.ID))
        output.append('Number of scans: {0}'.format(len(self.scans)))
        return '\n'.join(output)
