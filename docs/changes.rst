.. _changelog:

==========
Change Log
==========


Version 0.3
===========

> API Changes
-------------

- Scan object has new properties: `scan_type` and `emptyroom`.

> New Features
--------------

- MEG data with an associated empty room file now brings the data along when it is added to another BIDS folder hierarchy.


Version 0.2.1
=============

Date: 11th Feb 2019

> API Changes
-------------

- All functions in `bidshandler.utils` are now private with the exception of the new function `download_test_data`. (`#13 <https://github.com/Macquarie-MEG-Research/BIDSHandler/pull/13>`_)


Version 0.2
===========

Date: 5th Feb 2019

> API Changes
-------------

- `BIDSFolder` renamed to `BIDSTree`

> New Features
--------------

- Query functionality. (`#8 <https://github.com/Macquarie-MEG-Research/BIDSHandler/pull/8>`_)
- `BIDSTree` objects are able to have an `.xml` file generated to map out their entire structure. (`#4 <https://github.com/Macquarie-MEG-Research/BIDSHandler/pull/4>`_)
- EEG, fMRI and MRI data reading has been improved dramatically. (`#9 <https://github.com/Macquarie-MEG-Research/BIDSHandler/pull/9>`_)
