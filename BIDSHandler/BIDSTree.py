import os
import os.path as op
import xml.etree.ElementTree as ET

from .Project import Project
from .Subject import Subject
from .Session import Session
from .Scan import Scan
from .QueryMixin import QueryMixin
from .BIDSErrors import NoProjectError
from .utils import copyfiles, realize_paths, prettyprint_xml


class BIDSTree(QueryMixin):
    def __init__(self, fpath, initialize=True):
        super(BIDSTree, self).__init__()
        self.path = fpath
        self._projects = dict()

        self._queryable_types = ('project', 'subject', 'session', 'scan')

        if initialize:
            self._add_projects()

#region public methods

    def add(self, other, copier=copyfiles):
        """Add another Scan, Session, Subject, Project or BIDSTree to this
        object.

        Parameters
        ----------
        other : Instance of Scan, Session, Subject, Project or BIDSTree
            Object to be added to this BIDSTree.
            The added object must already exist in the same context as this
            object (except BIDSTree objects).
        copier : function
            A function to facilitate the copying of any applicable data.
            This function must have the call signature
            `function(src_files: list, dst_files: list)`
            Where src_files is the list of files to be moved and dst_files is
            the list of corresponding destinations.
            This will default to using utils.copyfiles which simply implements
            shutil.copy and creates any directories that do not already exist.
        """
        if isinstance(other, BIDSTree):
            # merge all child projects in
            for project in other.projects:
                self.add(project, copier)
        elif isinstance(other, Project):
            if other._id in self._projects:
                self.project(other._id).add(other, copier)
            else:
                new_project = Project._clone_into_bidstree(self, other)
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
                new_project = Project._clone_into_bidstree(self,
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
            raise TypeError("Cannot add a {0} object to a BIDSTree".format(
                other.__name__))

    def generate_map(self, output_file=None):
        """
        Generate a map of the BIDS folder.

        Parameters
        ----------
        output_file : str
            Path to write the file to.
            If not provided this will return the string representation.

        Returns
        -------
        String representation of xml structure.
        """
        root = ET.Element('BIDSTree', attrib={'path': self.path})
        for project in self.projects:
            root.append(project._generate_map())
        if output_file is None:
            return prettyprint_xml(ET.tostring(root, encoding='unicode'))
        dir_path = op.dirname(output_file)
        if dir_path != '':
            if not op.exists(dir_path):
                os.makedirs(op.dirname(output_file))
        with open(output_file, 'w') as file:
            file.write(prettyprint_xml(ET.tostring(root,
                                                   encoding='unicode')))

    def project(self, id_):
        """Return the Project corresponding to the provided id."""
        try:
            return self._projects[id_]
        except KeyError:
            raise NoProjectError("Project {0} doesn't exist in this "
                                 "BIDS folder".format(id_))

#region private methods

    def _add_projects(self):
        """Add all the projects in the folder to the BIDS folder."""
        projects = dict()
        for f in os.listdir(self.path):
            full_path = op.join(self.path, f)
            if op.isdir(full_path):
                projects[f] = Project(f, self)
        self._projects = projects

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
        return scan_list

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
        return subject_list

#region class methods

    def __contains__(self, other):
        """Determine if the Subject contains a certain Scan, Session, Subject
        or Project.

        Parameters
        ----------
        other : Instance of Scan, Session, Subject or Project
            Object to check whether it is contained in this BIDS folder.
        """
        if isinstance(other, Project):
            return other._id in self.projects
        elif isinstance(other, (Subject, Session, Scan)):
            for project in self.projects:
                if other in project:
                    return True
            return False
        else:
            raise TypeError("Can only determine if a Scan, Session or Subject "
                            "is contained.")

    def __iter__(self):
        return iter(self.projects)

    def __getitem__(self, item):
        """
        Return the child project with the corresponding name (if it exists).
        """
        return self.project(item)

    def __repr__(self):
        return '<BIDSTree, {0} project{1}, @ {2}>'.format(
            len(self.projects),
            ('s' if len(self.projects) > 1 else ''),
            self.path)

    def __str__(self):
        return "BIDS folder containing {0} projects".format(len(self.projects))
