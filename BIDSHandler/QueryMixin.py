from datetime import datetime

from .utils import compare, compare_times
from .QueryList import QueryList


class QueryMixin():
    """Provides query functionality to the various BIDS classes.

    This Mix-in class has no functionality on its own and can only be used
    as a sub-class.
    """

#region public methods

    def query(self, obj, token, condition, value):
        """
        Query the BIDS object and return the appropriate data.

        Parameters
        ----------
        obj : str
            The object type that should be returned.
            This can be one of ('project', 'subject', 'session', 'scan')
        token : str
            The key to query for. This can be a value from the following list:
             - `task`: Corresponds to the `task` key in the BIDS filename.
             - `acquisition` | `acq`: Corresponds to the `acq` key in the BIDS
                filename.
             - `run`: Corresponds to the `run` key in the BIDS filename.
             - `proc`: Corresponds to the `proc` key in the BIDS filename.
             - `age`: Corresponds to the age of the participant
                [Only available for `obj='subject'`]
             - `sex`: Corresponds to the gender of the participant.
                [Only available for `obj='subject'`]
             - `group`: Corresponds to the group of the participant.
                [Only available for `obj='subject'`]
             - `rec_date`: Corresponds to the time and date of the recording.
                The value can either be formatted like "%Y-%m-%d"
                (ie. YYYY-MM-DD) to specify a single day, or it can be
                specified to the second by formatting it using the format
                string "%Y-%m-%dT%H:%M:%S" (ie. YYYY-MM-DDTHH:mm:ss).
             - `subjects`: Corresponds to the number of subjects contained.
                [Only available for `obj='project'`]
             - `sessions`: Corresponds to the number of sessions contained.
                [Only available for `obj='project'` or `'subject'`]
             - `scans`: Corresponds to the number of scans contained.
                [Only available for `obj='project'`, `'subject'` or
                `'session'`]
             - Any other token will be considered to be a key in the
                sidecar.json file.
        condition : 'str'
            One of ('<', '<=', '=', '!=', '!!=' (none equal), '=>', '>').
            Used to perform comaprisons between the value provided and the
            values the data have.
            The '!!=' operator here is used to distinguish between the case of
            when you want to determine if something contains something that
            isn't the value you specify, and whether something doesn't contain
            the value specified.
            This operator is currently only supported for the tokens `'task'`,
            `'acquisition'`/`'acq', `'run'` and `'proc'`.
        value : str | int | float
            The value the token has (or the value to compare using the
            `condition` argument)
            The value provided must match exactly if the equality operator is
            used, and must have a type appropriate for comparison if an
            inequality operator is used.
            Currently regex is not supported, but this may come in the future.

        Returns
        -------
        list of objects.
        """
        if not self._allow_query(obj):
            raise ValueError('Invalid query')
        return_data = QueryList()
        # each token will be handled separately
        if token == 'subjects':
            # return projects with a certain number of subjects
            if obj != 'project':
                raise ValueError('Can only query the number of subjects for a '
                                 'project.')
            data = [project for project in self.projects if
                    compare(len(project.subjects), condition, value)]
            return_data.extend(data)
        elif token == 'sessions':
            # return projects or subjects with a certain number of sessions
            if obj == 'project':
                data = [project for project in self.projects if
                        compare(len(project.sessions), condition, value)]
            elif obj == 'subject':
                data = [subject for subject in self.subjects if
                        compare(len(subject.sessions), condition, value)]
            else:
                raise ValueError('Can only query the number of sessions for a '
                                 'project or subject.')
            return_data.extend(data)
        elif token == 'scans':
            # return projects, subjects or sessions with a certain number of
            # scans
            if obj == 'project':
                data = [project for project in self.projects if
                        compare(len(project.scans), condition, value)]
            elif obj == 'subject':
                data = [subject for subject in self.subjects if
                        compare(len(subject.scans), condition, value)]
            elif obj == 'session':
                data = [session for session in self.sessions if
                        compare(len(session.scans), condition, value)]
            else:
                raise ValueError('Can only query the number of scans for a '
                                 'project, subject or session.')
            return_data.extend(data)
        elif token in ('task', 'acquisition', 'run', 'proc', 'acq'):
            # condition can *only* be '=', '!=' or '!!='
            if condition not in ('=', '!=', '!!='):
                raise ValueError('Condition can only be "=" or "!=", "!!="')
            if obj == 'project':
                iter_obj = self.projects
            elif obj == 'subject':
                iter_obj = self.subjects
            elif obj == 'session':
                iter_obj = self.sessions
            elif obj == 'scan':
                iter_obj = None
            else:
                raise ValueError('Invalid obj specified')
            if iter_obj is not None:
                for ob in iter_obj:
                    if condition != '!!=':
                        for scan in ob.scans:
                            if compare(scan.__getattribute__(token), condition,
                                       value):
                                return_data.append(ob)
                                break
                    else:
                        # Find the list of obj's that do have the value for the
                        # token.
                        has_objs = self.query(obj, token, '=', value)
                        # Now find the inverse of this list.
                        return_data.extend(list(set(iter_obj) - set(has_objs)))
            else:
                for scan in self.scans:
                    if compare(scan.__getattribute__(token), condition, value):
                        return_data.append(scan)
        elif token == 'age':
            # obj can *only* be subject
            if obj != 'subject':
                raise ValueError('Can only return subject data when querying '
                                 'age.')
            for subj in self.subjects:
                if subj.age is not None and subj.age != 'n/a':
                    if compare(subj.age, condition, value):
                        return_data.append(subj)
        elif token == 'sex':
            # obj can *only* be subject
            if obj != 'subject':
                raise ValueError('Can only return subject data when querying '
                                 'sex.')
            # condition can *only* be '=' or '!='
            if condition not in ('=', '!='):
                raise ValueError('Condition can only be "=" or "!="')
            data = [subject for subject in self.subjects if
                    compare(subject.sex, condition, value)]
            return_data.extend(data)
        elif token == 'group':
            # obj can *only* be subject
            if obj != 'subject':
                raise ValueError('Can only return subject data when querying '
                                 'group.')
            # condition can *only* be '=' or '!='
            if condition not in ('=', '!='):
                raise ValueError('Condition can only be "=" or "!="')
            data = [subject for subject in self.subjects if
                    compare(subject.group, condition, value)]
            return_data.extend(data)
        elif token == 'rec_date':
            # The dates all need to be converted to date time objects so that
            # comparisons can be determined correctly.
            try:
                compare_date = datetime.strptime(value, "%Y-%m-%d")
                compare_date = compare_date.date()
            except ValueError:
                compare_date = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            if obj == 'project':
                iter_obj = self.projects
            elif obj == 'subject':
                iter_obj = self.subjects
            elif obj == 'session':
                iter_obj = self.sessions
            elif obj == 'scan':
                iter_obj = None
            else:
                raise ValueError('Invalid obj specified')
            if iter_obj is not None:
                for ob in iter_obj:
                    for scan in ob.scans:
                        dt = scan.acq_time
                        # convert to datetime object
                        dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
                        if compare_times(dt, condition, compare_date):
                            return_data.append(ob)
                            break
            else:
                for scan in self.scans:
                    dt = scan.acq_time
                    # convert to datetime object
                    dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")
                    if compare_times(dt, condition, compare_date):
                        return_data.append(scan)
        else:
            # We will assume any other value is a key in the sidecar.json
            # to allow these values to be searched for.
            if obj == 'project':
                iter_obj = self.projects
            elif obj == 'subject':
                iter_obj = self.subjects
            elif obj == 'session':
                iter_obj = self.sessions
            elif obj == 'scan':
                iter_obj = None
            else:
                raise ValueError('Invalid obj specified')
            if iter_obj is not None:
                for ob in iter_obj:
                    for scan in ob.scans:
                        sidecar_val = scan.info.get(token, None)
                        if sidecar_val is not None:
                            if compare(sidecar_val, condition, value):
                                return_data.append(ob)
                                break
            else:
                for scan in self.scans:
                    sidecar_val = scan.info.get(token, None)
                    if sidecar_val is not None:
                        if compare(sidecar_val, condition, value):
                            return_data.append(scan)
        return return_data

#region private methods

    def _allow_query(self, obj):
        """Determine whether the current class is able to process the query.

        Parameters
        ----------
        obj : str
            This can be one of ('project', 'subject', 'session', 'scan')
        """
        if obj in self._queryable_types:
            return True
        return False

#region properties

    @property
    def projects(self):
        return [self]

    @property
    def subjects(self):
        return [self]

    @property
    def sessions(self):
        return [self]

    @property
    def scans(self):
        return [self]

#region class methods

    def __contains__(self, other):  # pragma: no cover
        # to stop pylint complaining...
        pass
