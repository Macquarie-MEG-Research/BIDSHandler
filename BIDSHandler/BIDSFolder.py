import os
import os.path as op

from .Project import Project
from .Subject import Subject
from .Session import Session
from .Scan import Scan
from .BIDSErrors import MappingError, NoProjectError
from .utils import copyfiles


class BIDSFolder():
    def __init__(self, fpath, initialize=True):
        self.path = fpath
        self._projects = dict()

        if initialize:
            self.determine_content()

#region public methods

    def determine_content(self):
        """ return a list of all the BIDS projects in the specified folder """
        projects = dict()
        try:
            for f in os.listdir(self.path):
                full_path = op.join(self.path, f)
                if op.isdir(full_path):
                    projects[f] = Project(f, self)
        except MappingError:
            self._projects = dict()
        self._projects = projects

    def add(self, other, copier=copyfiles):
        #!INCOMPLETE
        """Add another Scan to this object.

        Parameters
        ----------
        other : Instance of BIDSFolder, Project, Subject Session or Scan
            Object to be added to this session.
            This can be any level of BIDS object.
        copier : function
            A function to facilitate the copying of any applicable data.
            This function must have the call signature
            `function(src_files: list, dst: string)`
            Where src_files is the list of files to be moved and dst is the
            destination folder.
            This will default to using utils.copyfiles which simply implements
            shutil.copy.
        """
        if isinstance(other, BIDSFolder):
            for project in other.projects:
                self.add(project, copier)
        elif isinstance(other, Project):
            if other._id in self._projects:
                self.project(other._id).add(other)
            else:
                # Add a new project.
                os.makedirs(op.join(self.path, other.ID))
                new_project = Project(other._id, self, initialize=False)
                # TODO: get file list etc.
        elif isinstance(other, Subject):
            # If the project the subject is a part of exists add the subject to
            # this project.
            if other.project._id in self._projects:
                self.project(other.project._id).add(other, copier)
            else:
                # Otherwise add a new project and add the subject to it.
                new_project = Project(other.project.ID, self,
                                      initialize=False)
                os.makedirs(op.join(self.path, other.project.ID))

        elif isinstance(other, Session):
            print('sess')
        elif isinstance(other, Scan):
            print('scan')
        else:
            raise TypeError("Cannot add a {0} object to a BIDSFolder".format(
                other.__name__))

    def project(self, id_):
        try:
            return self._projects[id_]
        except KeyError:
            raise NoProjectError("Project {0} doesn't exist in this "
                                 "BIDS folder".format(id_))

#region properties

    @property
    def projects(self):
        return list(self._projects.values())

    @property
    def subjects(self):
        subject_list = []
        for project in self.projects:
            subject_list.extend(project.subjects)

#region class methods

    def __repr__(self):
        return "BIDS folder containing {0} projects".format(len(self.projects))

    def __iter__(self):
        return iter(self.projects)
