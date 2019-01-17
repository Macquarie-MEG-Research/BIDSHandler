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

### Loading data

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

We can load this by passing the folder path location to the `BIDSTree` object:

```python
from BIDSHandler import BIDSTree

folder = BIDSTree('BIDSFOLDER')
```

This will load the folder, then recurse over the sub-folders and find all projects, subjects, sessions and (MEG) scans.

### Looking at individual sub-components

Each of the `BIDSTree`, `Project`, `Subject` and `Session` objects can be iterated over, to yield the child objects:

```python
for project in folder.projects:
  print(project)
# results:
# ID: PROJ01
# Number of subjects: 2
```

We can also pick out individual projects, subjects, session or scans:

```python
sub2 = folder.project('PROJ01').subject('02')
print(sub2)
# results (with made up values):
# ID: sub-02
# Age: 22
# Gender: M
# Group: Control
# Number of Sessions: 1

print(sub2.age)
# 22

ses1 = sub2.session('01')
print(ses1.scans_tsv)
# <base file path>/BIDSFOLDER/PROJ01/sub-02/ses-01/sub-02_ses-01_scans.tsv
```

### Adding/merging BIDS data

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
folder2 = BIDSTree('BIDSFOLDER2')
```

The data in this structure can be added to the previous `BIDSTree` in a number of different ways:
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

### Querying BIDS data

One very useful function to be able to perform on any large dataset is to be able to pull out or find the data corresponding to a set of conditions you may have.
`BIDSHandler` allows you to query data in a simple manner and extract a list of objects that you require.
To understand how this works we can look at the function used:

```python
BIDSTree.query(obj, token, condition, value)
```
You can see more information by reading the docstring (`help(BIDSTree.query)`), however we can summarise the process and meanings here.
 - `obj` is the name of the object type you want and can be one of `'project'`, `'subject'`, `'session'` or `'scan'`. The object name must be the of the same level as the object you are querying or lower.
 - `token` is the name of the data you want to compare. This can be a value like `'task'`, `'group'`, or `'sessions'` for example, or you can use any value that is used as a key in the sidecar.json file.
 To see the full list you can see the docstring by entering
 ```python
 from BIDSHandler import BIDSTree
 help(BIDSTree.query)
 ```
 - `condition` is one of `('<', '<=', '=', '!=', '!!=', '=>', '>')` where `'!!='` here means `none equal`. This is distinctly different from `'!='` in that if you ask for the list of subjects that do not contain `'task'=='resting'` using `'!='` you will get the list of all subjects that contains tasks that aren't `'task'=='resting'`. `'!!='` will however return the list of subjects that have no instances of `'task'=='resting'`.
 The `condition` must also be valid for the data type. So for example using a `condition` of `<` for a value that is a string will not return any meaningful result or may raise an error.
 - `value` is the value to check against.
 This value can either be the actual value in the file name, so for `token` = `'task'`, the value will be the string in `task-value`.
 For `token`'s such as `age` it will be the age found in the participant.tsv.

Because of the structure of the arguments, it is quite simple to construct queries, as well as read what it is expected that they ask.

All BIDS objects except the `Scans` object can be queried (ie. `BIDSTree`, `Project`, `Subject`, and `Session`), and only queries which make sense can be made on these objects. For example the question *"what are all the projects in this session that have one subject"* obviously makes no sense and will raise an error.

Queries can also be componded to allow for multiple queries to be chained.
This is possible because the object that the `query` function returns is actually a `QueryList` object which has all the functionality of a normal python list, however it also has a `query` method which can be called to apply a query to every member of the list.

#### Examples:

*Task:* Find a list of all subjects that are Female.

```python
folder2.query('subject', 'sex', '=', 'F')
```
If we let subjects 1 and 3 be female, then this would return the list of those two Subject objects.

*Task:* Find all the projects containing recordings after the 1st of January 2018:

```python
folder2.query('project', 'rec_date_', '>=', '2018-01-01')
```
When querying recording dates the date value *must* be in the format `YYYY-MM-DD` when specifying a particular date.

The date can also be specified to the second if need be by using a date value of the format `"%Y-%m-%dT%H:%M:%S"` (the previous date format is `"%Y-%m-%d"`).

*Task:* Find all the subjects that do not have any resting state tasks:

```python
folder2.query('subject', 'task', '!!=', 'restingstate')
```
Where a key-value pair in the BIDS filename of `task-restingstate` corresponds to resting state data.

*Task:* Find all the subjects that are female and that have 1 session:
First we will find all the subjects that are female, then we will find all the subjects in this list that have only one session.

```python
subjects = folder2.query('subject', 'sex', '=', 'F')
subjects.query('subject', 'sessions', '=', 1)
```

## Contributing

BIDSHandler is still in very early stages, but contributions are more than welcome in the form of PR's and by raising issues to discussion potential features.
Ideally BIDSHandler would be able to handle any BIDS data from any modality such as MRI and EEG, but the current focus is on MEG data.
