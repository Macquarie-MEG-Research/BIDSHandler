.. BIDSHandler documentation master file, created by
   sphinx-quickstart on Mon Feb  4 15:53:39 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

BIDSHandler Documentation
=======================================

BIDSHandler: A simple way to manage and manipulate BIDS compatible data.

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   api
   usage
.. toctree::
   :maxdepth: 1

   changes

Installation
============

`BIDSHandler` requires only one dependency which can be easily installed using `pip`::

    $ pip install pandas


To install `BIDSHandler` you can then enter in a terminal::

    $ pip install BIDSHandler


Entering `import bidshandler` in a python console should not raise an error which indicates that `BIDSHandler` has been installed correctly.

Basic Usage
===========

`BIDSHandler` has 5 primary objects; `BIDSTree`, `Project`, `Subject`, `Session` and `Scan`, corresponding to different levels within a BIDS archive folder structure.
Generally data will be loaded into a `BIDSTree` object and the child objects are automatically generated. From there it is easy to query and manipulate the BIDS data.

.. code:: python

    >>> import bidshandler as bh
    >>> tree = bh.BIDSTree('folder')
    >>> print(tree.projects)
    >>> # list of Project objects contained in the BIDSTree
    >>> print(tree.subjects)
    >>> # list of Subject objects contained in the BIDSTree
    >>> # etc.

