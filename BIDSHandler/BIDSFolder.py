import os
import os.path as op

from .Project import Project
from .Subject import Subject
from .Session import Session
from .Scan import Scan
from .BIDSErrors import MappingError, NoProjectError
from .utils import copyfiles, realize_paths


class BIDSFolder():
    def __init__(self, fpath, initialize=True):
        self.path = fpath
        self._projects = dict()

        if initialize:
            self.determine_content()

#region public methods

    def add(self, other, copier=copyfiles):
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
            # merge all child projects in
            for project in other.projects:
                self.add(project, copier)
        elif isinstance(other, Project):
            if other._id in self._projects:
                self.project(other._id).add(other, copier)
            else:
                new_project = Project._clone_into_bidsfolder(self, other)
                # copy over the description and readme:
                file_list = [other._description, other._readme]
                fl_left = realize_paths(other, file_list)
                fl_right = realize_paths(new_project, file_list)
                copier(fl_left, fl_right)
                new_project._description = other._description
                new_project._readme = other._readme
                new_project.add(other, copier)
                self._projects[other._id] = new_project

        elif isinstance(other, (Subject, Session, Scan)):
            # If the project the subject is a part of exists add the subject to
            # this project.
            if other.project._id in self._projects:
                self.project(other.project._id).add(other, copier)
            else:
                new_project = Project._clone_into_bidsfolder(self,
                                                             other.project)
                # copy over the description and readme:
                file_list = [other.project._description, other.project._readme]
                fl_left = realize_paths(other.project, file_list)
                fl_right = realize_paths(new_project, file_list)
                copier(fl_left, fl_right)
                new_project._description = other.project._description
                new_project._readme = other.project._readme
                new_project.add(other, copier)
                self._projects[other.project._id] = new_project
        else:
            raise TypeError("Cannot add a {0} object to a BIDSFolder".format(
                other.__name__))

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

    def project(self, id_):
        try:
            return self._projects[id_]
        except KeyError:
            raise NoProjectError("Project {0} doesn't exist in this "
                                 "BIDS folder".format(id_))

#region properties

    @property
    def projects(self):
        """List of all Projects contained in the BIDS folder."""
        return list(self._projects.values())

    @property
    def scans(self):
        """List of all Scans contained in the BIDS folder."""
        scan_list = []
        for project in self.projects:
            scan_list.extend(project.scans)

    @property
    def sessions(self):
        """List of all Sessions contained in the BIDS folder."""
        session_list = []
        for project in self.projects:
            session_list.extend(project.sessions)
        return session_list

    @property
    def subjects(self):
        """List of all Subjects contained in the BIDS folder."""
        subject_list = []
        for project in self.projects:
            subject_list.extend(project.subjects)

#region class methods

    def __iter__(self):
        return iter(self.projects)

    def __getitem__(self, item):
        """
        Return the child project with the corresponding name (if it exists).
        """
        return self.project(item)

    def __repr__(self):
        return "BIDS folder containing {0} projects".format(len(self.projects))
