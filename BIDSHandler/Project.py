import os.path as op
import os
import pandas as pd
from collections import OrderedDict

from .Subject import Subject
from .Session import Session
from .Scan import Scan
from .BIDSErrors import NoSubjectError, MappingError, AssociationError
from .utils import copyfiles, realize_paths


class Project():
    def __init__(self, id_, bids_folder, initialize=True):
        self._id = id_
        self.bids_folder = bids_folder
        self._participants_tsv = None
        self._description = None
        self._readme = None
        self._subjects = dict()

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
        elif isinstance(other, Subject):
            if self._id == other.project._id:
                if other in self:
                    self.subject(other._id).add(other, copier)
                else:
                    new_subject = Subject._clone_into_project(self, other)
                    new_subject.add(other, copier)
                    self._subjects[other._id] = new_subject
            else:
                raise AssociationError("subject", "project")
        elif isinstance(other, (Session, Scan)):
            if self._id == other.project._id:
                if other.subject in self:
                    # If the subject already exists add the session to it.
                    self.subject(other.subject._id).add(other, copier)
                else:
                    # Otherwise create a new subject and add the session to it.
                    new_subject = Subject._clone_into_project(self,
                                                              other.subject)
                    new_subject.add(other, copier)
                    self._subjects[other.subject._id] = new_subject
            else:
                if isinstance(other, Session):
                    raise AssociationError("session", "project")
                else:
                    raise AssociationError("scan", "project")
        else:
            raise TypeError("Cannot add a {0} object to a Subject".format(
                type(other).__name__))

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
            elif fname == 'dataset_description.json':
                self._description = fname
            elif fname == 'README.txt':
                self._readme = fname

    def create_empty_participants_tsv(self):
        """Create an empty participants.tsv file for this project."""
        self._participants_tsv = 'participants.tsv'
        full_path = realize_paths(self, self._participants_tsv)
        if not op.exists(full_path):
            df = pd.DataFrame(
                OrderedDict([
                    ('participant_id', []),
                    ('age', []),
                    ('sex', []),
                    ('group', [])]),
                columns=['participant_id', 'age', 'sex', 'group'])
        df.to_csv(full_path, sep='\t', index=False, na_rep='n/a',
                  encoding='utf-8')

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

    @staticmethod
    def _clone_into_bidsfolder(bids_folder, other):
        """Create a copy of the Project with a new parent BIDSFolder.

        Parameters
        ----------
        bids_folder : Instance of BIDSFolder
            New parent BIDSFolder.
        other : instance of Project
            Original Project instance to clone.
        """
        os.makedirs(realize_paths(bids_folder, other.ID), exist_ok=True)
        new_project = Project(other._id, bids_folder, initialize=False)
        new_project.create_empty_participants_tsv()
        return new_project

#region properties

    @property
    def description(self):
        if self._description is not None:
            return realize_paths(self, self._description)
        raise FileNotFoundError

    @property
    def ID(self):
        return str(self._id)

    @property
    def participants_tsv(self):
        if self._participants_tsv is not None:
            return realize_paths(self, self._participants_tsv)
        raise FileNotFoundError

    @property
    def path(self):
        """Determine path location based on parent paths."""
        return op.join(self.bids_folder.path, self.ID)

    @property
    def readme(self):
        if self._readme is not None:
            return realize_paths(self, self._readme)
        raise FileNotFoundError

    @property
    def sessions(self):
        """List of all Sessions contained in the Project."""
        session_list = []
        for subject in self.subjects:
            session_list.extend(subject.sessions)
        return session_list

    @property
    def scans(self):
        """List of all Scans contained in the Project."""
        scan_list = []
        for subject in self.subjects:
            scan_list.extend(subject.scans)
        return scan_list

    @property
    def subjects(self):
        """List of all Subjects contained in the Project."""
        return list(self._subjects.values())

#region class methods

    def __contains__(self, other):
        """Determine if the Subject contains a certain session or scan.

        Parameters
        ----------
        other : Instance of Scan, Session or Subject
            Scan, Session or Subject object to check whether it is contained by
            this Project.
        """
        if isinstance(other, Subject):
            return other._id in self._subjects
        elif isinstance(other, (Session, Scan)):
            for subject in self.subjects:
                if other in subject:
                    return True
            return False
        else:
            raise TypeError("Can only determine if a Scan, Session or Subject "
                            "is contained.")

    def __iter__(self):
        return iter(self._subjects.values())

    def __getitem__(self, item):
        """
        Return the child subject with the corresponding name (if it exists).
        """
        return self.subject(item)

    def __repr__(self):
        output = []
        output.append('ID: {0}'.format(self.ID))
        output.append('Number of subjects: {0}'.format(len(self.subjects)))
        return '\n'.join(output)
