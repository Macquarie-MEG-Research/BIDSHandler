# BIDSHandler
API for loading and processing BIDS-compatible folders.

## Installation

BIDSHandler is still in very early development, however it can be built by downloading the respository and building the wheel by entering the command
```
python setup.py sdist bdist_wheel
```

The wheel can then be installed using by entering the command
```
pip install BIDSHandler-0.1.dev0-py3-none-any.whl
```

A pre-built wheel may also be available in the releases tab, however in this early development stage it may not be the most recent version so it is generally best to build from the source.

## Usage

Loading a BIDS folder is very simple.

Imagine we have a BIDS folder with the following structure:
```
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
```

We can load this by passing the folder path location to the `BDISFolder` object:

```python
from BIDSHandler import BIDSFolder

folder = BIDSFolder('BIDSFOLDER')
```

This will load the folder, then recurse over the sub-folders and find all projects, subjects, sessions and (MEG) scans.
Each of these levels is an object itself, and they can be iterated over:

```python
for project in folder.projects:
  print(project)
# results:
# Project ID: PROJ01
# Number of subjects: 2
```

We can also pick out individual projects, subjects, session or scans:

```python
sub2 = folder.project('PROJ01').subject('02')
print(sub2)
# results (with made up values):
# sub-02
# Info:
# Age: 22
# Gender: M
# Group: Control
# Sessions: 1

print(sub2.age)
# 22

ses1 = sub2.session('01')
print(ses1.scans_tsv)
# <base file path>/BIDSFOLDER/PROJ01/sub-02/ses-01/sub-02_ses-01_scans.tsv
```

As well as loading in BIDS folders to read the data from them, we can also manipulate the BIDS folders.
This is particularly useful if BIDS data has to be merged if it is converted in multiple locations but all needs to be stored in the one location.
BIDSHandler is capable of merging BIDS data on any level into any other compatible level.
So a single session can be merged in, or entire projects can be merged.
If a single session is merged into a BIDS folder without the project or subject existing already it will be automatically generated so that the BIDS hierarchy is always complete and correct.

Adding in BIDS data is also as simple as a single command.
Consider a second BIDS file structure like:
```
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
```

We can load the folder as before:
```python
folder2 = BIDSFolder('BIDSFOLDER2')
```

The data in this structure can be added to the previous `BIDSFolder` in a number of different ways:
```python
proj2 = folder2.project('PROJ02')
sub3 = proj2.subject('03')
ses1 = sub3.session('01')

print(folder)
# BIDS folder containing 1 projects

# add the data to the other bids folder (pick one):
folder.add(folder2)
# OR
folder.add(proj2)
# OR
folder.add(sub3)
# OR
folder.add(ses1)

print(folder)
# BIDS folder containing 2 projects
```

This will automatically copy all the files over to the new location.
It is also possible to specify a custom copying function (default is minimally wrapped `shutils.copy` (enhanced to automatically create directories if they do not exist)).

```python
folder.add(folder2, copier=some_other_copy_function)
```
For more information and constraints on `copier` see the docstring for the `add` function.

## Contributing

BIDSHandler is still in very early stages, but contributions are more than welcome in the form of PR's.
Ideally BIDSHandler would be able to handle any BIDS data from any modality such as MRI and EEG, but the current focus is on MEG data.
