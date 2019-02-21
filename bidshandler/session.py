import os
import os.path as op
from collections import OrderedDict
import re
import shutil

import xml.etree.ElementTree as ET

import pandas as pd
from datetime import datetime

from .utils import (_get_bids_params, _copyfiles, _realize_paths, _combine_tsv,
                    _multi_replace, _fix_folderless, _file_list)
from .bidserrors import MappingError, AssociationError, NoScanError
from .scan import Scan
from .querymixin import QueryMixin


_RAW_FILETYPES = ('.nii', '.bdf', '.con', '.sqd')   # TODO: add more...


class Session(QueryMixin):
    """Session-level object.

    Parameters
    ----------
    id_ : str
        Id of the session. This is the sequence of characters after `'ses-'`.
    subject : :class:`bidshandler.Subject`
        Parent Subject object containing this Session.
    initialize : bool, optional
        Whether to parse the folder and load any child structures.
    no_folder : bool, optional
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

    def add(self, other, copier=_copyfiles):
        """.. # noqa

        Add another Scan or Session to this object.

        Parameters
        ----------
        other : Instance of :class:`bidshandler.Scan` or :class:`bidshandler.Session`
            Object to be added to this Session.
            The added object must already exist in the same context as this
            object.
        copier : function, optional
            A function to facilitate the copying of any applicable data.
            This function must have the call signature
            `function(src_files: list, dst_files: list)`
            Where src_files is the list of files to be moved and dst_files is
            the list of corresponding destinations.
            This will default to using utils._copyfiles which simply implements
            :py:func:`shutil.copy` and creates any directories that do not
            already exist.
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
            if not (self._id == other.session._id and
                    self.subject._id == other.subject._id and
                    self.project._id == other.project._id):
                raise AssociationError("scan", "project, subject and session")
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
            _combine_tsv(self.scans_tsv, other_scan_df, 'filename')

            # Assign as a set to avoid any potential doubling of the raw
            # file path.
            files = set(other.associated_files.values())
            files.add(other._sidecar)
            files.add(other._raw_file)
            # Copy the files over.
            fl_left = _realize_paths(other, files)
            fl_right = []
            for fpath in files:
                fl_right.append(op.join(self.path, other._path, fpath))
            copier(fl_left, fl_right)
            # Add the scan object to our scans list.
            scan = Scan(other.raw_file_relative, self,
                        acq_time=other.acq_time)
            self._scans.append(scan)

            # finally, check to see if the scan had an associated empty
            # room file. If so, make sure it comes along too
            if other.emptyroom is not None:
                self.project.add(other.emptyroom)
        else:
            raise TypeError("Cannot add a {0} object to a Subject".format(
                type(other).__name__))

    def contained_files(self):
        """Get the list of contained files.

        Returns
        -------
        file_list : list
            List with paths to all contained files relating to the BIDS
            structure.
        """
        file_list = set()
        file_list.add(_realize_paths(self, self._scans_tsv))
        for scan in self.scans:
            file_list.update(scan.contained_files())
        return file_list

    def delete(self):
        """Delete the session information."""
        for scan in self.scans[:]:
            # Delete the scan. This will remove it from this sessions' scan
            # list.
            scan.delete()
        os.remove(self.scans_tsv)
        if len(list(_file_list(self.path))) == 0:
            shutil.rmtree(self.path)

        # Remove this session from the session list in the subject and delete.
        del self.subject._sessions[self._id]

    def rename(self, id_):
        """Change the sessions' id.

        Parameters
        ----------
        id_ : str
            New id for the session object.
        """
        self._rename(self.subject._id, id_)

    def scan(self, task='.', acq='.', run='.', return_all=False):
        """Return a list of all contained Scan's corresponding to the provided
        values.

        Parameters
        ----------
        task : str
            Value of `task` in the BIDS filename.
        acq : str
            Value of `acq` in the BIDS filename.
        run : str
            Value of `run` in the BIDS filename.
        return_all : bool
            Whether to return every scan in the session that matches the
            provided values or not.

        Returns
        -------
        scan : list(:class:`bidshandler.Scan`)
            List of Scan's.

        Notes
        -----
        The `task`, `acq` and `run` arguments may all have regular expressions
        passed to them.
        """
        # First process any regular expressions passed:
        tsk_re = re.compile(task) if task is not None else re.compile('.')
        acq_re = re.compile(acq) if acq is not None else re.compile('.')
        run_re = re.compile(run) if run is not None else re.compile('.')
        valid_scans = list()
        for scan in self.scans:
            _task = scan.task if scan.task is not None else '.'
            _acq = scan.acq if scan.acq is not None else '.'
            _run = scan.run if scan.run is not None else '.'
            if (re.match(tsk_re, _task) and re.match(acq_re, _acq) and
                    re.match(run_re, _run)):
                valid_scans.append(scan)
        if return_all:
            return valid_scans
        else:
            if len(valid_scans) > 1:
                raise Exception("Multiple scans found for {0}. To get the "
                                "list set `return_all=True`".format(
                                    self.subject.ID))
            if valid_scans == []:
                raise NoScanError
            return valid_scans[0]

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
                filename_data = _get_bids_params(fname)
                if filename_data.get('file', None) == 'scans':
                    # Store the path and extract the paths of the scans.
                    self._scans_tsv = fname
                    scans = pd.read_csv(_realize_paths(self, self._scans_tsv),
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
                    rec_path = _realize_paths(self, rec_type)
                    if rec_type == 'fmap':
                        # fieldmap sequence
                        # The files with `file` = `magnitude1` are not raw
                        # scans.
                        filename_data = _get_bids_params(fname)
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
        """Check that there is at least one included scan."""
        if len(self._scans) == 0:
            raise MappingError("No scans found in {0}/{1}/{2}.".format(
                self.project.ID, self.subject.ID, self.ID))

    @staticmethod
    def _clone_into_subject(subject, other):
        """Create a copy of the Session with a new parent Subject.

        Parameters
        ----------
        subject : :class:`bidshandler.Subject`
            New parent Subject.
        other : :class:`BIDSHandler.Session`
            Original Session instance to clone.

        Returns
        -------
        new_session : :class:`bidshandler.Session`
            New uninitialized Session cloned from `other` to be a child of
            `subject`.
        """
        # set the directory to be the same as the parent.
        os.makedirs(_realize_paths(subject, other.ID), exist_ok=True)
        # Create a new empty session object.
        new_session = Session(other._id, subject, initialize=False)
        new_session._create_empty_scan_tsv()
        return new_session

    def _create_empty_scan_tsv(self):
        """Create an empty scans.tsv file for this session."""
        self._scans_tsv = '{0}_{1}_scans.tsv'.format(self.subject.ID, self.ID)
        full_path = _realize_paths(self, self._scans_tsv)
        if not op.exists(full_path):
            df = pd.DataFrame(OrderedDict([('filename', [])]),
                              columns=['filename'])
            df.to_csv(full_path, sep='\t', index=False, na_rep='n/a',
                      encoding='utf-8')

    def _generate_map(self):
        """Generate a map of the Session.

        Returns
        -------
        root : :py:class:`xml.etree.ElementTree.Element`
            Xml element containing session information.
        """
        root = ET.Element('Session', attrib={'ID': str(self._id)})
        for scan in self.scans:
            root.append(scan._generate_map())
        return root

    def _rename(self, subj_id, sess_id):
        """Change the session id for all contained files.

        Parameters
        ----------
        subj_id : str
            Raw subject ID value. Ie. *without* `sub-`.
        sess_id : str
            Raw session ID value. Ie. *without* `ses-`.
        """
        # cache current values and generate new ones for use
        old_subj_id = self.subject.ID
        new_subj_id = 'sub-{0}'.format(subj_id)
        old_sess_id = self.ID
        new_sess_id = 'ses-{0}'.format(sess_id)
        old_scans_tsv = self.scans_tsv
        old_path = self.path
        if self.has_no_folder:
            new_path = op.join(self.subject.path, new_sess_id)
        else:
            new_path = _multi_replace(old_path, [old_subj_id, old_sess_id],
                                      [new_subj_id, new_sess_id])
        if not op.exists(new_path):
            os.makedirs(new_path)

        scan_delete_paths = set()
        # call rename on each of the contained Scan objects
        for scan in self.scans:
            scan_delete_paths.add(scan.path)
            scan._rename(subj_id, sess_id)

        # update the row data to point to the new scan locations
        if old_scans_tsv is not None:
            if op.exists(old_scans_tsv):
                df = pd.read_csv(old_scans_tsv, sep='\t')
                for idx, row in enumerate(df['filename']):
                    row = _fix_folderless(self, row, old_sess_id, old_subj_id)
                    df.at[idx, 'filename'] = _multi_replace(
                        row, [old_subj_id, old_sess_id],
                        [new_subj_id, new_sess_id])
                df.to_csv(old_scans_tsv, sep='\t', index=False, na_rep='n/a',
                          encoding='utf-8')

            self._scans_tsv = _fix_folderless(self, self._scans_tsv,
                                              old_sess_id, old_subj_id)
            self._scans_tsv = _multi_replace(self._scans_tsv,
                                             [old_subj_id, old_sess_id],
                                             [new_subj_id, new_sess_id])

            # rename the scans.tsv file
            os.rename(old_scans_tsv, op.join(self.project.path, new_subj_id,
                                             new_sess_id, self._scans_tsv))

        # remove the old path
        # TODO: check to see if the folders are empty.
        for fpath in scan_delete_paths:
            shutil.rmtree(fpath)

        # change the internal id. self.ID -> new_sess_id
        old_id = self._id
        self._id = sess_id
        # update the parent subject dictionary
        if old_id != self._id:
            self.subject._sessions[self._id] = self
            del self.subject._sessions[old_id]
        if self._id != 'none':
            self.has_no_folder = False

#region properties

    @property
    def bids_tree(self):
        """Parent :class:`bidshandler.BIDSTree` object."""
        return self.project.bids_tree

    @property
    def date(self):
        """The recording date of the session.

        Returns
        -------
        known_date : :func:`datetime.date`
            Specific date of the year the session ocurred on.
        """
        known_date = None
        for scan in self.scans:
            # if the scan has an acquisition date, load it into a datetime.date
            # object and compare
            if scan.acq_time is not None:
                try:
                    compare_date = datetime.strptime(scan.acq_time, '%Y-%m-%d')
                except ValueError:
                    compare_date = datetime.strptime(scan.acq_time,
                                                     '%Y-%m-%dT%H:%M:%S')
                compare_date = compare_date.date()
                if known_date is None:
                    known_date = compare_date
                else:
                    if compare_date != known_date:
                        known_date = None
                        break
        return known_date

    @property
    def ID(self):
        """ID with 'ses' prefix."""
        return 'ses-{0}'.format(self._id)

    @property
    def inheritable_files(self):
        """List of files that are able to be inherited by child objects."""
        files = self.subject.inheritable_files
        for fname in os.listdir(self.path):
            abs_path = _realize_paths(self, fname)
            if op.isfile(abs_path):
                files.append(abs_path)
        return files

    @property
    def path(self):
        """Determine path location based on parent paths."""
        if self.has_no_folder:
            return self.subject.path
        return _realize_paths(self.subject, self.ID)

    @property
    def project(self):
        """Parent :class:`bidshandler.Project` object."""
        return self.subject.project

    @property
    def scans(self):
        """List of contained Scans."""
        return self._scans

    @property
    def scans_tsv(self):
        """Absolute path of associated scans.tsv file."""
        _path = None
        if self._scans_tsv is not None:
            _path = _realize_paths(self, self._scans_tsv)
        return _path

#region class methods

    def __contains__(self, other):
        """Determine whether the Session object contains a scan.

        Parameters
        ----------
        other : :class:`bidshandler.Scan`
            Object to test whether it is contained in this Session.

        Returns
        -------
        bool
            Returns True if the object is contained within this Session.
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
            ('s' if len(self.scans) != 1 else ''),
            self.path)

    def __str__(self):
        output = []
        output.append('ID: {0}'.format(self.ID))
        output.append('Number of scans: {0}'.format(len(self.scans)))
        return '\n'.join(output)
