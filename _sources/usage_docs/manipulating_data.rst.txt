.. manipulating_data:

======================
Manipulating BIDS data
======================

Adding/merging BIDS data
========================

As well as loading in BIDS folders to read the data from them, we can also manipulate the BIDS folders.
This is particularly useful if BIDS data has to be merged if it is converted in multiple locations but all needs to be stored in the one location.
BIDSHandler is capable of merging BIDS data on any level into any other compatible level.
So a single session can be merged in, or entire projects can be merged.
If a single session is merged into a BIDS folder without the project or subject existing already it will be automatically generated so that the BIDS hierarchy is always complete and correct.

Adding in BIDS data is also as simple as a single command.
Consider a second BIDS file structure like::

    BIDSFOLDER2
    └ PROJ02
    └ sub-03
        └ ses-01
        └ meg
            └ <raw files and metadata such as sidecar, channels.tsv etc.>
        └ sub-03_ses-01_scans.tsv
    └ dataset_description.json
    └ participants.tsv
    └ README.txt


We can load the folder as before:

.. code:: python

    >>> folder2 = BIDSTree('BIDSFOLDER2')


The data in this structure can be added to the previous `BIDSTree` in a number of different ways:

.. code:: python

    >>> proj2 = folder2.project('PROJ02')
    >>> sub3 = proj2.subject('03')
    >>> ses1 = sub3.session('01')
    >>> print(folder)
    BIDS folder containing 1 projects
    >>> # add the data to the other bids folder (pick one):
    >>> folder.add(folder2)
    >>> # OR
    >>> folder.add(proj2)
    >>> # OR
    >>> folder.add(sub3)
    >>> # OR
    >>> folder.add(ses1)
    >>> print(folder)
    BIDS folder containing 2 projects

This will automatically copy all the files over to the new location.
It is also possible to specify a custom copying function (default is minimally wrapped :py:func:`shutil.copy` (enhanced to automatically create directories if they do not exist)).

.. code:: python

    >>> folder.add(folder2, copier=some_other_copy_function)

For more information and constraints on `copier` see :func:`bidshandler.BIDSTree.BIDSTree.add`
