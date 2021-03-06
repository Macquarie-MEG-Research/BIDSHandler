import os
import os.path as op
from collections import OrderedDict
import xml.etree.ElementTree as ET
import shutil
from warnings import warn

import pandas as pd

from .bidserrors import MappingError, NoSessionError, AssociationError
from .session import Session
from .scan import Scan
from .querymixin import QueryMixin
from .utils import _copyfiles, _realize_paths, _file_list


class Subject(QueryMixin):
    """Subject-level object.

    Parameters
    ----------
    id_ : str
        Id of the subject. This is the sequence of characters after `'sub-'`.
    project : :class:`bidshandler.Project`
        Parent Project object containing this Subject.
    initialize : bool, optional
        Whether to parse the folder and load any child structures.
    """
    def __init__(self, id_, project, initialize=True):
        super(Subject, self).__init__()
        self._id = id_
        self.project = project
        # Contained sessions
        self._sessions = dict()

        # All the various information about the subject from the
        # participants.tsv file.
        self.subject_data = OrderedDict()

        self._queryable_types = ('subject', 'session', 'scan')

        if initialize:
            self._load_subject_info()
            self._add_sessions()
            self._check()

#region public methods

    def add(self, other, copier=_copyfiles):
        """.. # noqa

        Add another Scan, Session or Subject to this object.

        Parameters
        ----------
        other : Instance of :class:`bidshandler.Scan`, :class:`bidshandler.Session` or :class:`bidshandler.Subject`
            Object to be added to this Subject.
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
        if isinstance(other, Subject):
            # If the subject has the same ID, take all the child sessions and
            # merge into this project.
            if self._id == other._id:
                for session in other.sessions:
                    self.add(session, copier)
            else:
                raise ValueError("Added subject must have same ID.")
        elif isinstance(other, Session):
            if not (self._id == other.subject._id and
                    self.project._id == other.project._id):
                raise AssociationError("session", "project and subject")
            if other in self:
                # if the other session being added has the same ID, merge it
                # with the current session with that ID.
                self.session(other._id).add(other, copier)
            else:
                # Check to see if we have only one scan without a session
                # folder:
                if len(self.sessions) == 1:
                    # If we have only one existing session, we want to
                    # check whether the existing session has no actual
                    # session folder.
                    if self.sessions[0].has_no_folder:
                        warn("Current Subject has only one session with no "
                             "specified session id. Please set this "
                             "sessions' id by renaming it using "
                             "`self.sessions[0].rename(1)` (or other number). "
                             "The session to be added will not be added.")
                        return
                new_session = Session._clone_into_subject(self, other)
                new_session.add(other, copier)
                self._sessions[other._id] = new_session

        elif isinstance(other, Scan):
            if not (self._id == other.subject._id and
                    self.project._id == other.project._id):
                raise AssociationError("scan", "project and subject")

            if other.session in self:
                self.session(other.session._id).add(other, copier)
            else:
                new_session = Session._clone_into_subject(self,
                                                          other.session)
                new_session.add(other, copier)
                self._sessions[other.session._id] = new_session
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
        for session in self.sessions:
            file_list.update(session.contained_files())
        return file_list

    def delete(self):
        """Delete the subject from the parent Project."""
        for session in self.sessions[:]:
            session.delete()
        # remove the subject information from the participants.tsv
        if self.project.participants_tsv is not None:
            df = pd.read_csv(self.project.participants_tsv, sep='\t')
            row_idx = df[df['participant_id'] == self.ID].index.item()
            df = df.drop(row_idx)
            df.to_csv(self.project.participants_tsv, sep='\t', index=False,
                      na_rep='n/a', encoding='utf-8')

        if len(list(_file_list(self.path))) == 0:
            shutil.rmtree(self.path)

        del self.project._subjects[self._id]

    def rename(self, id_):
        """Change the subjects' id.

        Parameters
        ----------
        id_ : str
            New id for the subject object.
        """
        self._rename(id_)

    def session(self, id_):
        """Return the Session corresponding to the provided id.

        Parameters
        ----------
        id_ : str
            Id of the session to return. This doesn't need the `'ses'` prefix.

        Returns
        -------
        :class:`bidshandler.Session`
            Contained Session with the specified `id_`.
        """
        try:
            return self._sessions[str(id_)]
        except KeyError:
            raise NoSessionError(
                "Session {0} doesn't exist in subject '{1}'. "
                "Possible sessions: {2}".format(id_, self.ID,
                                                list(self._sessions.keys())))

#region private methods

    def _add_sessions(self):
        """Add all the sessions in the folder to the Subject."""
        for fname in os.listdir(self.path):
            full_path = op.join(self.path, fname)
            if op.isdir(full_path) and 'ses' in fname:
                ses_id = fname.split('-')[1]
                self._sessions[ses_id] = Session(ses_id, self)
        # If we haven't found any sub-folders with 'ses' in their name try and
        # assume that the current folder is in fact the session folder (ie.
        # only one session).
        if len(self._sessions) == 0:
            self._sessions['none'] = Session('none', self, no_folder=True)

    def _check(self):
        """Check that there is at least one included session."""
        if len(self._sessions) == 0:
            raise MappingError("No sessions found in {0}/{1}.".format(
                self.project.ID, self.ID))

    @staticmethod
    def _clone_into_project(project, other):
        """Create a copy of the Subject with a new parent Project.

        Parameters
        ----------
        project : :class:`bidshandler.Project`
            New parent Project.
        other : :class:`bidshandler.Subject`
            Original Subject instance to clone.

        Returns
        -------
        new_subject : :class:`bidshandler.Subject`
            New uninitialized Subject cloned from `other` to be a child of
            `project`.
        """
        os.makedirs(_realize_paths(project, other.ID), exist_ok=True)

        # Create a new empty subject object.
        new_subject = Subject(other._id, project, initialize=False)

        # Merge the subject data into the participants.tsv file.
        df = pd.read_csv(project.participants_tsv, sep='\t')
        data = [('participant_id', [other.ID])]
        for key, value in other.subject_data.items():
            data.append((key, [value]))
        other_sub_df = pd.DataFrame(
            OrderedDict(data),
            columns=['participant_id', *other.subject_data.keys()])
        df = df.append(other_sub_df, sort=False)
        df.to_csv(project.participants_tsv, sep='\t', index=False,
                  na_rep='n/a', encoding='utf-8')

        # Check if the new parent has a participants.json file.
        # If not, give it the one with this subject if it has one.
        if project._participants_json is not None:
            if other.project._participants_json is not None:
                shutil.copy(other.project.participants_json,
                            project.path)

        # can now safely get the subject info
        new_subject._load_subject_info()
        return new_subject

    def _load_subject_info(self):
        participant_path = op.join(op.dirname(self.path), 'participants.tsv')
        if not op.exists(participant_path):
            return
        participants = pd.read_csv(participant_path, sep='\t')
        column_names = set(participants.columns.values)
        if 'participant_id' not in column_names:
            # temporary error... This means the file is bad.
            raise MappingError
        column_names.remove('participant_id')
        row = participants.loc[participants['participant_id'] == self.ID]
        for col_name in column_names:
            val = row.get(col_name)
            if val is not None:
                if not val.empty:
                    # Ignore empty rows.
                    self.subject_data[col_name] = val.item()
            else:
                self.subject_data[col_name] = "n/a"

    def _generate_map(self):
        """Generate a map of the Subject.

        Returns
        -------
        root : :py:class:`xml.etree.ElementTree.Element`
            Xml element containing subject information.
        """
        attribs = {'ID': str(self._id)}
        attribs.update(zip(self.subject_data.keys(),
                           [str(x) for x in self.subject_data.values()]))
        for key, value in attribs.items():
            if value == 'n/a':
                attribs.pop(key)
        root = ET.Element('Subject', attrib=attribs)
        for session in self.sessions:
            root.append(session._generate_map())
        return root

    def _rename(self, subj_id):
        """Change the session id for all contained files.

        Parameters
        ----------
        subj_id : str
            Raw subject ID value. Ie. *without* `sub-`.
        """
        # cache current values
        old_subj_id = self.ID
        new_subj_id = 'sub-{0}'.format(subj_id)
        old_path = self.path
        new_path = self.path.replace(old_subj_id, new_subj_id)
        if not op.exists(new_path):
            os.mkdir(new_path)

        # call rename on each of the contained Scan objects
        for session in self.sessions:
            session._rename(subj_id, session._id)

        if op.exists(self.project.participants_tsv):
            df = pd.read_csv(self.project.participants_tsv, sep='\t')
            for idx, row in enumerate(df['participant_id']):
                if row == old_subj_id:
                    df.at[idx, 'participant_id'] = new_subj_id
                    break
            df.to_csv(self.project.participants_tsv, sep='\t', index=False,
                      na_rep='n/a', encoding='utf-8')

        # remove the old path
        if len(list(_file_list(old_path))) == 0:
            shutil.rmtree(old_path)
        else:
            warn_msg = "The following files haven't been moved correctly:\n{0}"
            warn(warn_msg.format(
                "\n".join(
                    [_realize_paths(self, p) for p in os.listdir(old_path)])))

        self._id = subj_id


#region properties

    @property
    def bids_tree(self):
        """Parent :class:`bidshandler.BIDSTree` object."""
        return self.project.bids_tree

    @property
    def ID(self):
        """ID with 'sub' prefix."""
        return 'sub-{0}'.format(self._id)

    @property
    def inheritable_files(self):
        """List of files that are able to be inherited by child objects."""
        # TODO: make private?
        files = self.project.inheritable_files
        for fname in os.listdir(self.path):
            abs_path = _realize_paths(self, fname)
            if op.isfile(abs_path):
                files.append(abs_path)
        return files

    @property
    def path(self):
        """Path of Subject folder."""
        return op.join(self.project.path, self.ID)

    @property
    def scans(self):
        """List of all contained :class:`bidshandler.Scan`'s.

        Returns
        -------
        list of :class:`bidshandler.Scan`
            All Scans within this Subject.
        """
        scan_list = []
        for session in self.sessions:
            scan_list.extend(session.scans)
        return scan_list

    @property
    def sessions(self):
        """List of all contained :class:`bidshandler.Session`'s.

        Returns
        -------
        list of :class:`bidshandler.Session`
            All Sessions within this Subject.
        """
        return list(self._sessions.values())

#region class methods

    def __contains__(self, other):
        """.. # noqa

        Determine if the Subject contains a certain Scan or Session.

        Parameters
        ----------
        other : Instance of :class:`bidshandler.Scan` or :class:`bidshandler.Session`
            Object to check whether it is contained in this Subject.

        Returns
        -------
        bool
            Returns True if the object is contained within this Subject.
        """
        if isinstance(other, Session):
            return other._id in self._sessions
        elif isinstance(other, Scan):
            for session in self.sessions:
                if other in session:
                    return True
            return False
        raise TypeError("Can only determine if Scans or Sessions are "
                        "contained.")

    def __iter__(self):
        """Iterable of the contained Session objects."""
        return iter(self._sessions.values())

    def __getitem__(self, item):
        """
        Return the child session with the corresponding name (if it exists).
        """
        return self.session(item)

    def __repr__(self):
        return '<Subject, ID: {0}, {1} session{2}, @ {3}>'.format(
            self.ID,
            len(self.sessions),
            ('s' if len(self.sessions) != 1 else ''),
            self.path)

    def __str__(self):
        output = []
        output.append('ID: {0}'.format(self.ID))
        for key, value in self.subject_data.items():
            output.append('{0}: {1}'.format(key.title(), value))
        output.append('Number of Sessions: {0}'.format(len(self.sessions)))
        return '\n'.join(output)
