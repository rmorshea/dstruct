# DStruct
Map raw data onto the defined fields of a dict-like structure

## Instalation
`dstruct` can be installed from GitHub using `pip`:

```
$ pip install git+https://github.com/rmorshea/dstruct.git#egg=dstruct
```

## Purpose
`dstruct` is designed to map a larger data structure onto a smaller one, which is simple
in principle, but can be complicated in practice - very robust datasets can have a degrees
of nesting, or information that's relivant to a specific use case, can be spread across
multiple fields.

## Basic Usage
`dstruct` is meant to make trimming aand parsing data down to bite-size chunks easy and
intuitive. In the simplest case, if we're only interested in information that resides,
at the leaves of a nested data set, it's straightforward to create a `DataStruct` that
will get it for you:

```python
# we're only interested in the
# values at "a", "c", and "d"
raw_data = {
    "a": 1,
    "b": {
        "c": 2,
        "d": 3
    }
}
```

```python
from dstruct import DataStruct, DataField

class A(DataStruct):
    
    # this is the same as:
    # a = DataField('a')
    a = DataField()
    # the constructor's arguments should 
    # be a path to values in the raw data
    c = DataField('b', 'c')
    d = DataField('b', 'd')

print(A(raw_data))
```

The `DataField` class is used to specify where the data your interested ins resides, and under
what field name it will exist at in the `DataStruct`. The arguments in a `DataField`'s
constructor should be a path to the relivant value in the raw data.

Once you've created your `DataStruct` class, simply pass it raw data to analyze, and you're done:
```python
# the printed data structure:
{"a": 1, "c": 2, "d": 3}
```

Once the instance has been created:

+ its fields can be retrieved and set with `.` or `dict` syntax
+ use its `update` method to give it new data to sift through

###But what about more complicated cases?
After all, a more realistic application of `dstruct` might be towards making a bank account summary.
And in that case, some parsers might be required for the information to be as clean and understandable
as possible. Adding a parser to a field can be done in a three ways:

**1. Using the keyword `"parser"` in a DataField:**

```python
raw_data = {'name': 'checking',
            'number': '123456789'}

class Account(DataStruct):
    name = DataField()
    # adds a parser that only shows the last four numbers
    number = DataField(parser=lambda s: 'X'*len(s[:-4])+s[-4:])

print(Card(raw_data))
```
```python
{'name': 'checking', 'number': 'XXXXX6789'}
```

**2. Using the `datafield` decorator:**

```python
raw_data = {'name': 'checking',
            'card-number': '0123456789'}

class Account(DataStruct):
    name = DataField()
    # creates a new DataField object with the
    # defined instance method as its parser
    @datafield('number')
    def number(self, numstr):
        return 'X'*len(numstr[:-4])+numstr[-4:]

print(Card(raw_data))
```
```python
{'name': 'checking', 'number': 'XXXXX6789'}
```

**3. Using the `dataparser` decorator:**

```python
raw_data = {'checking': '123456789',
            'credit': '987654321'}

class Accounts(DataStruct):
    def __init__(self, shown):
        self.number_shown = shown

    # creates a loose data parser
    # that is an instance method
    @dataparser
    def hide(self, numstr):
        n = self.number_shown
        return 'X'*len(numstr[:-n])+numstr[-n:]
    
    # the loose data parser can now
    # be used in multiple fields
    checking = DataField(parser=hide)
    credit = DataField(parser=hide)

print(Card(raw_data))
```
```python
{'name': 'checking', 'number': 'XXXXX6789'}
```

## Loading Files

At the moment, `dstruct` knows how to import data from json and from csv files. To load one of these file
types, all you have to do is create a data structure that inherits from the respective `DataStructFromJSON`
or `DataStructFromCSV` class, and pass its constructor a filename and path.

The generic class for loading files is `LoadedDataStruct`. Using this requires a `Loader` object to be
passed to its constructor. To create a custom loader, inherit from `dstruct.loader.Loader` and override
its `_read_file_as_dict` method.

## Examples

1. [`examples/basic.ipynb`]
(https://github.com/rmorshea/dstruct/blob/master/examples/basic.ipynb)
2. [`examples/advanced.ipynb`]
(https://github.com/rmorshea/dstruct/blob/master/examples/advanced.ipynb)
