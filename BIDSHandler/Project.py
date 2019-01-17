import os.path as op
import os
import pandas as pd
from collections import OrderedDict
import xml.etree.ElementTree as ET

from .Subject import Subject
from .Session import Session
from .Scan import Scan
from .QueryMixin import QueryMixin
from .BIDSErrors import NoSubjectError, MappingError, AssociationError
from .utils import copyfiles, realize_paths


class Project(QueryMixin):
    def __init__(self, id_, bids_tree, initialize=True):
        super(Project, self).__init__()
        self._id = id_
        self.bids_tree = bids_tree
        self._participants_tsv = None
        self._description = None
        self._readme = None
        self._subjects = dict()

        self._queryable_types = ('project', 'subject', 'session', 'scan')

        if initialize:
            self._add_subjects()
            self._check()

#region public methods

    def add(self, other, copier=copyfiles):
        """Add another Scan, Session, Subject or Project to this object.

        Parameters
        ----------
        other : Instance of Scan, Session, Subject or Project
            Object to be added to this Project.
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
        if isinstance(other, Project):
            # If the project has the same ID, take all the child subjects and
            # merge into this project.
            if self._id == other._id:
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

    def contained_files(self):
        """Get the list of contained files."""
        file_list = set()
        file_list.add(self.participants_tsv)
        file_list.add(self.readme)
        file_list.add(self.description)
        for subject in self.subjects:
            file_list.update(subject.contained_files())
        return file_list

    def subject(self, id_):
        """Return the Subject in this project with the corresponding ID."""
        try:
            return self._subjects[str(id_)]
        except KeyError:
            raise NoSubjectError(
                "Subject {0} doesn't exist in project {1}. "
                "Possible subjects: {2}".format(id_, self.ID,
                                                list(self._subjects.keys())))

#region private methods

    def _add_subjects(self):
        """Add all the subjects in the folder to the Project."""
        for fname in os.listdir(self.path):
            full_path = op.join(self.path, fname)
            if op.isdir(full_path) and 'sub-' in fname:
                sub_id = fname.split('-')[1]
                self._subjects[sub_id] = Subject(sub_id, self)
            elif fname == 'participants.tsv':
                self._participants_tsv = fname
            elif fname == 'dataset_description.json':
                self._description = fname
            elif fname == 'README.txt':
                self._readme = fname

    def _check(self):
        """Check that there are some subjects."""
        if len(self._subjects) == 0:
            raise MappingError

    @staticmethod
    def _clone_into_bidstree(bids_tree, other):
        """Create a copy of the Project with a new parent BIDSTree.

        Parameters
        ----------
        bids_tree : Instance of BIDSTree
            New parent BIDSTree.
        other : instance of Project
            Original Project instance to clone.
        """
        os.makedirs(realize_paths(bids_tree, other.ID), exist_ok=True)
        new_project = Project(other._id, bids_tree, initialize=False)
        new_project._create_empty_participants_tsv()
        return new_project

    def _create_empty_participants_tsv(self):
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

    def _generate_map(self):
        """Generate a map of the Project."""
        root = ET.Element('Project', attrib={'ID': str(self._id)})
        for subject in self.subjects:
            root.append(subject._generate_map())
        return root

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
        return op.join(self.bids_tree.path, self.ID)

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
        """Determine if the Project contains a certain Scan, Session or
        Project.

        Parameters
        ----------
        other : Instance of Scan, Session or Subject
            Object to check whether it is contained in this Project.
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
        return '<Project, ID: {0}, {1} subject{2}, @ {3}>'.format(
            self.ID,
            len(self.subjects),
            ('s' if len(self.subjects) > 1 else ''),
            self.path)

    def __str__(self):
        output = []
        output.append('ID: {0}'.format(self.ID))
        output.append('Number of subjects: {0}'.format(len(self.subjects)))
        return '\n'.join(output)
