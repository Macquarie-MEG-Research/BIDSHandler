# BIDSHandler
A simple way to manage and manipulate BIDS compatible data.

## Installation

`BIDSHandler` requires only one dependency which can be easily installed using `pip`:

```
pip install pandas
```

To install `BIDSHandler` you can then enter in a terminal:

```
pip install BIDSHandler
```

Entering `import bidshandler` in a python console should not raise an error which indicates that `BIDSHandler` has been installed correctly.

## Basic Usage

`BIDSHandler` has 5 primary objects; `BIDSTree`, `Project`, `Subject`, `Session` and `Scan`, corresponding to different levels within a BIDS archive folder structure.
Generally data will be loaded into a `BIDSTree` object and the child objects are automatically generated. From there it is easy to query and manipulate the BIDS data.

```python
import bidshandler as bh
tree = bh.BIDSTree('folder')
print(tree.projects)
print(tree.subjects)
# etc.
```

## Contributing

BIDSHandler is still in very early stages, but contributions are more than welcome in the form of PR's and by raising issues to discussion potential features.
Ideally BIDSHandler would be able to handle any BIDS data from any modality such as MRI and EEG, but the current focus is on MEG data.
