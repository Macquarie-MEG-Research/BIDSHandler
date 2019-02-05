.. loading_data:

=================
Loading BIDS data
=================

Loading
=======

Loading a BIDS folder is very simple.

Imagine we have a BIDS folder with the following structure::

    BIDSFOLDER
    └ PROJ01
    └ sub-01
        └ ses-01
        └ meg
            └ <raw files and metadata such as sidecar, channels.tsv etc.>
        └ sub-01_ses-01_scans.tsv
        └ ses-02
        └ meg
            └ <raw files and metadata such as sidecar, channels.tsv etc.>
        └ sub-01_ses-02_scans.tsv
    └ sub-02
        └ ses-01
        └ meg
            └ <raw files and metadata such as sidecar, channels.tsv etc.>
        └ sub-02_ses-01_scans.tsv
    └ dataset_description.json
    └ participants.tsv
    └ README.txt


We can load this by passing the folder path location to the `BIDSTree` object:

.. code:: python

    >>> from BIDSHandler import BIDSTree
    >>> folder = BIDSTree('BIDSFOLDER')


This will load the folder, then recurse over the sub-folders and find all projects, subjects, sessions and (MEG) scans.

Looking at individual sub-components
====================================

Each of the `BIDSTree`, `Project`, `Subject` and `Session` objects can be iterated over, to yield the child objects:

.. code:: python

    >>> for project in folder.projects:
    >>>     print(project)
    ID: PROJ01
    Number of subjects: 2


We can also pick out individual projects, subjects, session or scans:

.. code:: python

    >>> sub2 = folder.project('PROJ01').subject('02')
    >>> print(sub2)
    ID: sub-02
    Age: 22
    Gender: M
    Group: Control
    Number of Sessions: 1
    >>> print(sub2.age)
    22
    >>> ses1 = sub2.session('01')
    >>> print(ses1.scans_tsv)
    /BIDSFOLDER/PROJ01/sub-02/ses-01/sub-02_ses-01_scans.tsv
