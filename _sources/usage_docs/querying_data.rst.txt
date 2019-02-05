.. querying_data:

==================
Querying BIDS data
==================

One very useful function to be able to perform on any large dataset is to be able to pull out or find the data corresponding to a set of conditions you may have.
`BIDSHandler` allows you to query data in a simple manner and extract a list of objects that you require.
To understand how this works we can look at the function used:

.. code:: python

    >>> BIDSTree.query(obj, token, condition, value)


For the full details on allowed values etc see :func:`bidshandler.QueryMixin.QueryMixin.query`.
We will however summarise the process and meanings here.

- `obj` is the name of the object type you want and can be one of `'project'`, `'subject'`, `'session'` or `'scan'`. The object name must be the of the same level as the object you are querying or lower.
- `token` is the name of the data you want to compare. This can be a value like `'task'`, `'group'`, or `'sessions'` for example, or you can use any value that is used as a key in the sidecar.json file.
    To see the full list you can see the docstring by entering

    .. code:: python

        >>> from BIDSHandler import BIDSTree
        >>> help(BIDSTree.query)

- `condition` is one of `('<', '<=', '=', '!=', '!!=', '=>', '>')` where `'!!='` here means `none equal`. This is distinctly different from `'!='` in that if you ask for the list of subjects that do not contain `'task'=='resting'` using `'!='` you will get the list of all subjects that contains tasks that aren't `'task'=='resting'`. `'!!='` will however return the list of subjects that have no instances of `'task'=='resting'`.
    The `condition` must also be valid for the data type. So for example using a `condition` of `<` for a value that is a string will not return any meaningful result or may raise an error.
- `value` is the value to check against.
    This value can either be the actual value in the file name, so for `token` = `'task'`, the value will be the string in `task-value`.
    For `token`'s such as `age` it will be the age found in the participant.tsv.

Because of the structure of the arguments, it is quite simple to construct queries, as well as read what it is expected that they ask.

All BIDS objects can be queried, and only queries which make sense can be made on these objects. For example the question "what are all the projects in this session that have one subject" obviously makes no sense and will raise an error.

Queries can also be componded to allow for multiple queries to be chained.
This is possible because the object that the `query` function returns is actually a `QueryList` object which has all the functionality of a normal python list, however it also has a `query` method which can be called to apply a query to every member of the list.

Examples
========

**Task:** Find a list of all subjects that are Female.

.. code:: python

    >>> folder2.query('subject', 'sex', '=', 'F')


If we let subjects 1 and 3 be female, then this would return the list of those two Subject objects.

**Task:** Find all the projects containing recordings after the 1st of January 2018:

.. code:: python

    >>> folder2.query('project', 'rec_date_', '>=', '2018-01-01')


When querying recording dates the date value *must* be in the format `YYYY-MM-DD` when specifying a particular date.

The date can also be specified to the second if need be by using a date value of the format `"%Y-%m-%dT%H:%M:%S"` (the previous date format is `"%Y-%m-%d"`).

**Task:** Find all the subjects that do not have any resting state tasks:

.. code:: python

    >>> folder2.query('subject', 'task', '!!=', 'restingstate')


Where a key-value pair in the BIDS filename of `task-restingstate` corresponds to resting state data.

*Task:* Find all the subjects that are female and that have 1 session:
First we will find all the subjects that are female, then we will find all the subjects in this list that have only one session.

.. code:: python

    >>> subjects = folder2.query('subject', 'sex', '=', 'F')
    >>> subjects.query('subject', 'sessions', '=', 1)
