import os.path as op
import os
import pandas as pd
from collections import OrderedDict
import xml.etree.ElementTree as ET

from .subject import Subject
from .session import Session
from .scan import Scan
from .querymixin import QueryMixin
from .bidserrors import NoSubjectError, MappingError, AssociationError
from .utils import _copyfiles, _realize_paths


class Project(QueryMixin):
    """Project-level object

    Parameters
    ----------
    id_ : str
        Id of the project. This is the name of the folder containing the data.
    bids_tree : :class:`bidshandler.BIDSTree`
        Parent BIDSTree object containing this Project.
    initialize : bool, optional
        Whether to parse the folder and load any child structures.
    """
    def __init__(self, id_, bids_tree, initialize=True):
        super(Project, self).__init__()
        self._id = id_
        self.bids_tree = bids_tree
        self._participants_tsv = None
        self._participants_json = None
        self._description = None
        self._readme = None
        self._subjects = dict()

        self._queryable_types = ('project', 'subject', 'session', 'scan')

        if initialize:
            self._add_subjects()
            self._check()

#region public methods

    def add(self, other, copier=_copyfiles):
        """.. # noqa

        Add another Scan, Session, Subject or Project to this object.

        Parameters
        ----------
        other : Instance of :class:`bidshandler.Scan`, :class:`bidshandler.Session`, :class:`bidshandler.Subject` or :class:`bidshandler.Project`
            Object to be added to this Project.
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
        """Get the list of contained files.

        Returns
        -------
        file_list : list
            List with paths to all contained files relating to the BIDS
            structure.
        """
        file_list = set()
        file_list.add(self.participants_tsv)
        file_list.add(self.readme)
        file_list.add(self.description)
        for subject in self.subjects:
            file_list.update(subject.contained_files())
        return file_list

    def subject(self, id_):
        """Return the Subject in this project with the corresponding ID.

        Parameters
        ----------
        id_ : str
            Id of the subject to return.

        Returns
        -------
        :class:`bidshandler.Subject`
            Contained Subject with the specified `id_`.
        """
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
            elif fname == 'participants.json':
                self._participants_json = fname
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
        bids_tree : :class:`bidshandler.BIDSTree`
            New parent BIDSTree.
        other : :class:`BIDSHandler.Project`
            Original Project instance to clone.

        Returns
        -------
        new_project : :class:`bidshandler.Project`
            New uninitialized Project cloned from `other` to be a child of
            `bids_tree`.
        """
        os.makedirs(_realize_paths(bids_tree, other.ID), exist_ok=True)
        new_project = Project(other._id, bids_tree, initialize=False)
        new_project._create_empty_participants_tsv()
        return new_project

    def _create_empty_participants_tsv(self):
        """Create an empty participants.tsv file for this project."""
        self._participants_tsv = 'participants.tsv'
        full_path = _realize_paths(self, self._participants_tsv)
        if not op.exists(full_path):
            df = pd.DataFrame(
                OrderedDict([('participant_id', [])]),
                columns=['participant_id'])
        df.to_csv(full_path, sep='\t', index=False, na_rep='n/a',
                  encoding='utf-8')

    def _generate_map(self):
        """Generate a map of the Project.

        Returns
        -------
        root : :py:class:`xml.etree.ElementTree.Element`
            Xml element containing project information.
        """
        root = ET.Element('Project', attrib={'ID': str(self._id)})
        for subject in self.subjects:
            root.append(subject._generate_map())
        return root

#region properties

    @property
    def description(self):
        """Path to the associated description if there is one."""
        _path = None
        if self._description is not None:
            _path = _realize_paths(self, self._description)
        return _path

    @property
    def ID(self):
        """ID of the Project."""
        return str(self._id)

    @property
    def inheritable_files(self):
        """List of files that are able to be inherited by child objects."""
        # TODO: make private?
        files = []
        for fname in os.listdir(self.path):
            abs_path = _realize_paths(self, fname)
            if op.isfile(abs_path):
                files.append(abs_path)
        return files

    @property
    def participants_json(self):
        """Path to the associated participants.tsv if there is one."""
        _path = None
        if self._participants_json is not None:
            _path = _realize_paths(self, self._participants_json)
        return _path

    @property
    def participants_tsv(self):
        """Path to the associated participants.tsv if there is one."""
        _path = None
        if self._participants_tsv is not None:
            _path = _realize_paths(self, self._participants_tsv)
        return _path

    @property
    def path(self):
        """Path to Project folder."""
        return op.join(self.bids_tree.path, self.ID)

    @property
    def readme(self):
        """Path to the associated README.txt if there is one."""
        _path = None
        if self._readme is not None:
            _path = _realize_paths(self, self._readme)
        return _path

    @property
    def sessions(self):
        """List of all contained :class:`bidshandler.Session`'s.

        Returns
        -------
        list of :class:`bidshandler.Session`
            All Sessions within this Project.
        """
        session_list = []
        for subject in self.subjects:
            session_list.extend(subject.sessions)
        return session_list

    @property
    def scans(self):
        """List of all contained :class:`bidshandler.Scan`'s.

        Returns
        -------
        list of :class:`bidshandler.Scan`
            All Scans within this Project.
        """
        scan_list = []
        for subject in self.subjects:
            scan_list.extend(subject.scans)
        return scan_list

    @property
    def subjects(self):
        """List of all contained :class:`bidshandler.Subject`'s.

        Returns
        -------
        list of :class:`bidshandler.Subject`
            All Subjects within this Project.
        """
        return list(self._subjects.values())

#region class methods

    def __contains__(self, other):
        """.. # noqa

        Determine if the Project contains a certain Scan, Session or Project.

        Parameters
        ----------
        other : Instance of :class:`bidshandler.Scan`, :class:`bidshandler.Session` or :class:`bidshandler.Subject`
            Object to check whether it is contained in this Project.

        Returns
        -------
        bool
            Returns True if the object is contained within this Project.
        """
        if isinstance(other, Subject):
            return other._id in self._subjects
        elif isinstance(other, (Session, Scan)):
            for subject in self.subjects:
                if other in subject:
                    return True
            return False
        raise TypeError("Can only determine if a Scan, Session or Subject is"
                        "contained.")

    def __iter__(self):
        """Iterable of the contained Subject objects."""
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
            ('s' if len(self.subjects) != 1 else ''),
            self.path)

    def __str__(self):
        output = []
        output.append('ID: {0}'.format(self.ID))
        output.append('Number of subjects: {0}'.format(len(self.subjects)))
        return '\n'.join(output)
