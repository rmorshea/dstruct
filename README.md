# DStruct
Map raw data onto the defined fields of a dict-like structure

## Instalation and Testing
`dstruct` can be installed from GitHub using `pip`:

```
$ pip install git+https://github.com/rmorshea/dstruct.git#egg=dstruct
```

To run the tests, `cd` into the root directory of the package and run

```
$ nose2
```

## Purpose
`dstruct` is designed to map a larger data structure onto a smaller one, which is simple in
principle, but can be complicated in practice - sifting though robust datasets is difficult
when the structure is highly nested, or relivant information is fractured. However, `dstruct`'s
intuitive api makes pruning useless data, and parsing its relivant subsets easy.

## Basic Usage
In the simplest case, `dstruct` can retrieve the leaves of a nested data set.

To solve this problem, create a `DataStruct` with `DataField` [descriptors](https://docs.python.org/howto/descriptor.html).
The `DataField` class is used to specify where the data for that field resides, and the
attribute name it will be assigned to on the `DataStruct`. The arguments in a `DataField`'s
constructor should be the path to a relivant value in the raw data that gets passed to its
`DataStruct`.

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

# pass raw data to A's constructor
print(A(raw_data))
```

```
{'a': 1, 'c': 2, 'd': 3}
```

Once the instance has been created:

+ its fields can be retrieved and set with `.` or `dict` syntax
+ use its `update` method to give it new data to sift through

###But what about more complicated cases?
After all, a more realistic application of `dstruct` might be towards making a bank account summary.
And in that scenario, some parsers might be required to make the information presentable. Adding a
parser to the field of a `DataStruct` can be done in a three ways:

**1. Using the keyword `"parser"` in a DataField:**

```python
raw_data = {'name': 'checking',
            'number': '123456789'}

class Account(DataStruct):
    name = DataField()
    # adds a parser that only shows the last four numbers
    number = DataField(parser=lambda s: 'X'*len(s[:-4])+s[-4:])

print(Account(raw_data))
```
```
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

print(Account(raw_data))
```
```
{'name': 'checking', 'number': 'XXXXX6789'}
```

**3. Using the `dataparser` decorator:**

```python
raw_data = {'checking': '123456789',
            'credit': '987654321'}

class Accounts(DataStruct):
    def __init__(self, shown):
        self.number_shown = shown

    checking = DataField()

    # creates a loose data parser and use args
    # to specify which fields it applies to
    @dataparser('checking')
    def hide(self, numstr):
        n = self.number_shown
        return 'X'*len(numstr[:-n])+numstr[-n:]
    
    # alternatively pass the loose data
    # parser to a new field in kwargs
    credit = DataField(parser=hide)
    

print(Accounts(raw_data))
```
```
{'name': 'checking', 'number': 'XXXXX6789'}
```

see [examples](https://github.com/rmorshea/dstruct#examples) for more info

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
