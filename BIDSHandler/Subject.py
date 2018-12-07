import os
import os.path as op
from collections import OrderedDict

import pandas as pd

from .BIDSErrors import MappingError, NoSessionError, AssociationError
from .Session import Session
from .Scan import Scan
from .utils import copyfiles, realize_paths


class Subject():
    def __init__(self, id_, project, initialize=True):
        self._id = id_
        self.project = project
        # Contained sessions
        self._sessions = dict()

        self.age = 'n/a'
        self.sex = 'n/a'
        self.group = 'n/a'

        if initialize:
            self.get_subject_info()
            self.add_sessions()
            self._check()

#region public methods

    def add(self, other, copier=copyfiles):
        """Add another Session or Scan to this object.

        Parameters
        ----------
        other : Instance of Subject, Session or Scan
            Scan or Session object to be added to this Subject.
            The object must previously exist in the same project and subject
            as this current subject.
        copier : function
            A function to facilitate the copying of any applicable data.
            This function must have the call signature
            `function(src_files: list, dst: string)`
            Where src_files is the list of files to be moved and dst is the
            destination folder.
            This will default to using utils.copyfiles which simply implements
            shutil.copy.
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
            if (self._id == other.subject._id and
                    self.project._id == other.project._id):
                # If the session doesn't already exist, add it.
                if other not in self:
                    new_session = Session.clone_into_subject(self, other)
                # Otherwise simply use the existing session.
                else:
                    new_session = self.session(other._id)
                # For every scan in the added session, add to the new one.
                for scan in other.scans:
                    new_session.add(scan, copier)
                new_session._check()
                # Only add the new session to the list if it is indeed new.
                if other._id not in self._sessions:
                    self._sessions[other._id] = new_session
            else:
                raise AssociationError("session", "project and subject")
        elif isinstance(other, Scan):
            if (self._id == other.subject._id and
                    self.project._id == other.project._id):
                if other.session in self:
                    self.session(other.session._id).add(other, copier)
                else:
                    new_session = Session.clone_into_subject(self,
                                                             other.session)
                    new_session.add(other, copier)
                    new_session._check()
                    self._sessions[other.session._id] = new_session
            else:
                raise AssociationError("scan", "project and subject")
        else:
            raise TypeError("Cannot add a {0} object to a Subject".format(
                type(other).__name__))

    def add_sessions(self):
        for fname in os.listdir(self.path):
            full_path = op.join(self.path, fname)
            if op.isdir(full_path) and 'ses' in fname:
                ses_id = fname.split('-')[1]
                self._sessions[ses_id] = Session(ses_id, self)

    @staticmethod
    def clone_into_project(project, other):
        """Create a copy of the Subject with a new parent Project.

        Parameters
        ----------
        project : Instance of Project
            New parent Project.
        other : instance of Subject
            Original Subject instance to clone.
        """
        os.makedirs(realize_paths(project, other.ID), exist_ok=True)

        # Create a new empty subject object.
        new_subject = Subject(other._id, project, initialize=False)

        # Merge the subject data into the participants.tsv file.
        df = pd.read_csv(project.participants_tsv, sep='\t')
        other_sub_df = pd.DataFrame(
            OrderedDict([
                ('participant_id', [other.ID]),
                ('age', [other.age]),
                ('sex', [other.sex]),
                ('group', [other.group])]),
            columns=['participant_id', 'age', 'sex', 'group'])
        df = df.append(other_sub_df)
        df.to_csv(project.participants_tsv, sep='\t', index=False,
                  na_rep='n/a', encoding='utf-8')
        # can now safely get the subject info
        new_subject.get_subject_info()
        return new_subject

    def contained_files(self):
        """Get the list of contained files."""
        file_list = set()
        for session in self.sessions:
            file_list.update(session.contained_files())
        return file_list

    def get_subject_info(self):
        participant_path = op.join(op.dirname(self.path), 'participants.tsv')
        if not op.exists(participant_path):
            raise MappingError
        participants = pd.read_csv(participant_path, sep='\t')
        for i in range(len(participants)):
            row = participants.iloc[i]
            if row['participant_id'] == self.ID:
                self.age = row.get('age', 'n/a')
                self.sex = row.get('sex', 'n/a')
                self.group = row.get('group', 'n/a')
                break
        pass

    def session(self, id_):
        try:
            return self._sessions[str(id_)]
        except KeyError:
            raise NoSessionError(
                "Session {0} doesn't exist in subject '{1}'. "
                "Possible sessions: {2}".format(id_, self.ID,
                                                list(self._sessions.keys())))

#region private methods

    def _check(self):
        if len(self._sessions) == 0:
            raise MappingError

#region properties

    @property
    def bids_folder(self):
        """Parent BIDSFolder object."""
        return self.project.bids_folder

    @property
    def ID(self):
        """ID with 'sub' prefix."""
        return 'sub-{0}'.format(self._id)

    @property
    def path(self):
        """Determine path location based on parent paths."""
        return op.join(self.project.path, self.ID)

    @property
    def sessions(self):
        """List of contained Sessions."""
        return list(self._sessions.values())

    @sessions.setter
    def sessions(self, other):
        self.add(other)

    @property
    def scans(self):
        """List of contained Scans."""
        scan_list = []
        for session in self.sessions:
            scan_list.extend(session.scans)
        return scan_list

#region class methods

    def __contains__(self, other):
        """Determine if the Subject contains a certain session or scan.

        Parameters
        ----------
        other : Instance of Scan or Session
            Scan or Session object to check whether it is contained by this
            subject.
        """
        if isinstance(other, Session):
            if other._id in self._sessions:
                return True
            return False
        elif isinstance(other, Scan):
            for session in self.sessions:
                if other in session:
                    return True
            return False
        else:
            raise TypeError("Can only determine if Scans or Sessions are "
                            "contained.")

    def __iter__(self):
        return iter(self._sessions.values())

    def __repr__(self):
        output = []
        output.append(self.ID)
        output.append('Info:')
        output.append('Age: {0}'.format(self.age))
        output.append('Gender: {0}'.format(self.sex))
        output.append('Group: {0}'.format(self.group))
        output.append('Sessions: {0}'.format(len(self.sessions)))
        return '\n'.join(output)
