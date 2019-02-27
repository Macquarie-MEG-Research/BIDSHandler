.. _changelog:

==========
Change Log
==========


Version 0.3
===========

> API Changes
-------------

- Scan object has new properties: `scan_type` and `emptyroom`. (`#14 <https://github.com/Macquarie-MEG-Research/BIDSHandler/pull/14>`_)
- Searching for a `Scan` within a `Session` can now accept regex and is able to return more than one scan if multiple match. (`#15 <https://github.com/Macquarie-MEG-Research/BIDSHandler/pull/15>`_)

> New Features
--------------

- MEG data with an associated empty room file now brings the data along when it is added to another BIDS folder hierarchy. (`#14 <https://github.com/Macquarie-MEG-Research/BIDSHandler/pull/14>`_)


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
