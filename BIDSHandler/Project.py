import os.path as op
import os

from .Subject import Subject
from .Session import Session
from .Scan import Scan
from .BIDSErrors import NoSubjectError, MappingError
from .utils import copyfiles, realize_paths


class Project():
    def __init__(self, id_, bids_folder, initialize=True):
        self.ID = self._id = id_
        self.bids_folder = bids_folder
        self._participants_tsv = None
        self._subjects = dict()
        self.description = 'None'

        if initialize:
            self.add_subjects()
            self._check()

#region public methods

    def add(self, other, copier=copyfiles):
        """Add another Subject, Session or Scan to this object.

        Parameters
        ----------
        other : Instance of Project, Subject, Session or Scan
            Scan, Session or Subject object to be added to this Project.
            The object must previously exist in the same context.
        copier : function
            A function to facilitate the copying of any applicable data.
            This function must have the call signature
            `function(src_files: list, dst: string)`
            Where src_files is the list of files to be moved and dst is the
            destination folder.
            This will default to using utils.copyfiles which simply implements
            shutil.copy.
        """
        if isinstance(other, Project):
            # If the project has the same ID, take all the child subjects and
            # merge into this project.
            if self.ID == other.ID:
                for subject in other.subjects:
                    self.add(subject, copier)
            else:
                raise ValueError("Added project must have same ID.")
        if isinstance(other, Subject):
            if self._id == other.project.id:
                if other._id not in self._subjects:
                    new_subject = Subject.clone_into_project(self, other)
                else:
                    new_subject = self.subject(other._id)
                for session in other.sessions:
                    new_subject.add(session, copier)
                new_subject._check()
                # Add the new subject to the list of subjects.
                if other._id not in self._subjects:
                    self._subjects[other._id] = new_subject
            else:
                raise ValueError("Cannot add a subject from a different "
                                 "project.")
        if isinstance(other, Session):
            if self._id == other.project._id:
                # If the subject already exists add the session to it.
                if other.subject in self:
                    self.subject(other.subject._id).add(other, copier)
                else:
                    # Otherwise create a new subject and add the session to it.
                    new_subject = Subject.clone_into_project(self,
                                                             other.subject)
                    new_subject.add(other, copier)
                    self._subjects[other.subject._id] = new_subject
            else:
                raise ValueError("Cannot add a session from a different "
                                 "project.")
        elif isinstance(other, Scan):
            if self._id == other.project._id:
                if other.subject in self:
                    if other.session in self.subject(other.subject._id):
                        self.subject(other.subject._id).session(
                            other.session._id).add(other, copier)
                    else:
                        # Create a new session.
                        new_session = Session.clone_into_subject(
                            self.subject(other.subject._id),
                            other.session)
                        new_session.add(other, copier)
                        new_session._check()
                        self.subject(other.subject._id)._sessions[
                            other.session._id] = new_session
                else:
                    # Create a new subject.
                    new_subject = Subject.clone_into_project(self,
                                                             other.subject)
                    new_session = Session.clone_into_subject(new_subject,
                                                             other.session)
            else:
                raise ValueError("Cannot add a session from a different "
                                 "project.")

    def add_subjects(self):
        """Add all the subjects in the folder to the Project."""
        for fname in os.listdir(self.path):
            full_path = op.join(self.path, fname)
            # TODO: use utils.get_bids_params?
            if op.isdir(full_path) and 'sub-' in fname:
                sub_id = fname.split('-')[1]
                self._subjects[sub_id] = Subject(sub_id, self)
            elif fname == 'participants.tsv':
                self._participants_tsv = fname

    @staticmethod
    def clone_into_bidsfolder(bids_folder, other):
        """Create a copy of the Project with a new parent BIDSFolder.

        Parameters
        ----------
        bids_folder : Instance of BIDSFolder
            New parent BIDSFolder.
        other : instance of Project
            Original Project instance to clone.
        """
        os.makedirs(realize_paths(bids_folder, other.ID), exist_ok=True)
        return Project(other._id, bids_folder, initialize=False)

    def subject(self, id_):
        """Return the Subject in this project with the corresponding ID."""
        try:
            return self._subjects[str(id_)]
        except KeyError:
            raise NoSubjectError(
                "Subject {0} doesn't exist in project {1}. "
                "Possible subjects: {2}".format(id_, self.ID,
                                                list(self._subjects.keys())))

    def query(self, **kwargs):
        # return any data within the project that matches the kwargs given.
        pass

    def contained_files(self):
        """Get the list of contained files."""
        file_list = set()
        # TODO: add readme and dataset_description.json
        file_list.add(realize_paths(self, self.participants_tsv))
        for subject in self.subjects:
            file_list.update(subject.contained_files())
        return file_list

#region private methods

    def _check(self):
        """Check that there aren't no subjects."""
        if len(self._subjects) == 0:
            raise MappingError

#region properties

    @property
    def participants_tsv(self):
        return realize_paths(self, self._participants_tsv)

    @property
    def path(self):
        """Determine path location based on parent paths."""
        return op.join(self.bids_folder.path, self.ID)

    @property
    def scans(self):
        scan_list = []
        for subject in self.subjects:
            scan_list.extend(subject.scans)
        return scan_list

    @property
    def subjects(self):
        return list(self._subjects.values())

    @subjects.setter
    def subjects(self, other):
        self.add(other)

#region class methods

    def __contains__(self, other):
        """ other: instance of Subject """
        if isinstance(other, Subject):
            return other._id in self._subjects
        else:
            #TODO: allow checks for sessions and scans
            raise TypeError("Can only determine if a subject is contained.")

    def __iter__(self):
        return iter(self._subjects.values())

    def __repr__(self):
        output = []
        output.append('Project ID: {0}'.format(self.ID))
        output.append('Number of subjects: {0}'.format(len(self.subjects)))
        return '\n'.join(output)
