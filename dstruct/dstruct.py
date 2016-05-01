
import types
import utils
import loader as lod
import json
import os

class FieldError(Exception): pass

class StructEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, DataStruct):
            return obj._field_data 
        else:
            return super(StructEncoder, self).default(obj)

# - - - - - - - - - - - - - - - - -
# Field Destriptors For DataStructs
# - - - - -- -- - - - - - - - - - -

class BaseField(object):

    this_name = None

    def setup_self(self, name):
        self.this_name = name

    def setup_cls(self, cls):
        pass

    def setup_inst(self, inst):
        pass

    def __get__(self, inst, cls=None):
        if inst is None:
            return self
        else:
            try:
                return inst._field_data[self.this_name]
            except KeyError:
                m = "The field '%s' is empty"
                raise FieldError(m % (self.this_name, inst.__class__.__name__))

    def __set__(self, inst, value):
        inst._field_data[self.this_name] = value


class dataparser(object):

    def __init__(self, func):
        """A decorator for data parsers that are instance methods

        Example
        -------
        ```
        raw_data = {'mother': 'Alice',
                    'father': 'Steve',
                    'child': 'Daniel'}

        class Family(DataStruct):
            def __init__(self, lastname):
                self.lastname = lastname

            @dataparser
            def fullname(self, firstname):
                return firstname + ' ' + self.lastname

            mother = DataField('mother', parser=fullname)
            father = DataField('father', parser=fullname)
            child = DataField('child', parser=fullname)

        f = Family('Jones')
        f.update(raw_data)
        print(f)

        # printed data structure:
        # {'mother': 'Alice Jones', 'father': 'Steve Jones', 'child': 'Daniel Jones'}
        ```
        """
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __get__(self, inst, cls=None):
        if inst is None:
            return self
        else:
            return types.MethodType(self.func, inst, None)


class DataField(BaseField):

    def __init__(self, *path, **kwargs):
        """Defines a field for data within a :class:`DataStruct`

        Parameters
        ----------
        path: tuple
            The path to a value within a raw piece of data. If no path is provided
            the path is assumed to be ``(self.this_name)`` where ``self.this_name``
            is that of the attribute this field was defined under.
        **kwargs:
            By explicitely claiming ``path=None``, no assumptions are made about the
            ``path``, causing all the raw data to be passed to the handler for parsing.
            Asserting ``parser=<callable>`` creates a parser for this data field. The
            parser should accept one argument, that being the value at the ``path``
            in a raw piece of data.
        """
        self.data_path = path or kwargs.get('path', True)
        p = kwargs.get('parser')
        if callable(p) or p is None:
            self.parser = p
        else:
            raise ValueError("parser must be callable")

    def __call__(self, func):
        """Sets up a function as a `dataparser`"""
        self.parser = dataparser(func)
        return self

    def setup_cls(self, cls):
        """setup this field object on the given ``cls``"""
        if self.data_path is not None:
            # setup field in mapped paths
            d = cls._field_paths
            for key in self.data_path:
                if key in d:
                    sub = d[key]
                else:
                    sub = {}
                    d[key] = sub
                d = sub

            if None in d:
                l = d[None]
            else:
                l = []
                d[None] = l
            l.append(self.this_name)

    def setup_self(self, name):
        super(DataField, self).setup_self(name)
        if self.data_path is True:
            self.data_path = (self.this_name,)
        if self.data_path is None:
            self.data_path = ()

    def setup_inst(self, inst):
        if self.this_name in inst._field_parsers:
            m = "Conflicting parser found for the data structure field '%s'"
            raise FieldError(m % self.this_name)
        elif self.parser is not None:
            if isinstance(self.parser, dataparser):
                p = self.parser.__get__(inst)
            else:
                p = self.parser
            inst._field_parsers[self.this_name] = p
        super(DataField, self).setup_inst(inst)

def datafield(*path, **kwargs):
    """A decorator that defines a field for data within a :class:`DataStruct`

    The decorated function becomes the parser for a :class:`DataField` which
    will be assigned to a data structure under the function's defined name.

    Parameters
    ----------
    path: tuple
        The path to a value within a raw piece of data. If no path is provided
        the path is assumed to be ``(self.this_name)`` where ``self.this_name``
        is that of the attribute this field was defined under.
    **kwargs:
        By explicitely claiming ``path=None``, no assumptions are made about the
        ``path``, causing all the raw data to be passed to the handler for parsing.
    """
    return DataField(*path, **kwargs)

# - - - - - - - - - - - - -
# Base Data Structure Class
# - - - - -- -- - - - - - -

class MetaStruct(type):

    def __init__(cls, name, bases, classdict):
        # paths within raw data that map to
        # the fields of the data structure
        cls._field_paths = {}

        super(MetaStruct, cls).__init__(name, bases, classdict)

        cdict = {}
        for c in cls.mro()[::-1]:
            cdict.update(c.__dict__)
        # setup_cls the fields of subclasses
        for k, v in cdict.items():
            if isinstance(v, BaseField):
                v.setup_self(k)
                v.setup_cls(cls)


# use `utils.with_metaclass` for py3 compatibility
class DataStruct(utils.with_metaclass(MetaStruct, object)):

    def __new__(cls, data=None):
        inst = super(DataStruct, cls).__new__(cls)
        # the fields of the data structure
        # and their corresponding parsers
        inst._field_parsers = {}
        # where field values are stored
        inst._field_data = {}

        for k, v in cls.__dict__.items():
            if isinstance(v, BaseField):
                v.setup_inst(inst)

        return inst

    def __init__(self, data=None):
        """Map raw data onto the defined fields of this dict-like structure"""
        self.update(data)

    def __setitem__(self, key, value):
        f = self.getfield(key)
        f.__set__(self, key, value)

    def __getitem__(self, key):
        f = self.getfield(key)
        f.__get__(self, key)

    def delfield(self, field):
        f = self.getfield(field)

        d = self._field_paths
        path = d.data_path

        for k in path:
            d = d[k]
        l = d[None]
        l.remove(f.this_name)

        # clean up
        if len(l)==0:
            del d[None]
            d = self._field_paths
            for k in path:
                last = d
                d = last[k]
                if len(d) == 0:
                    del last[k]
                    break

        del self._field_data[p.this_name]

    def update(self, data=None):
        if data is not None:
            if isinstance(data, DataStruct):
                data = data._field_data
            mapped = self._map_data_to_fields(data)
            for field, value in mapped.items():
                if field in self._field_parsers:
                    value = self._field_parsers[field](value)
                setattr(self, field, value)

    def _map_data_to_fields(self, data):
        mapped = {}
        paths = self._field_paths
        val_iter = utils.parallel_dict_iter(paths, data)
        for path_value, data_value in val_iter:
            for field in path_value[None]:
                mapped[field] = data_value
        return mapped

    def getfield(self, name):
        try:
            f = getattr(self.__class__, name)
        except:
            raise FieldError("No field '%s'" % name)
        if isinstance(f, BaseField):
            return f
        else:
            raise FieldError("The attribute '%s' is not a field" % name)

    def hasfield(self, name):
        return isinstance(getattr(self.__class__, name, None), BaseField)

    def add_fields(self, **fields):
        """Dynamically add fields to this DataStruct instance."""
        self.__class__ = type(self.__class__.__name__, (self.__class__,), fields)

    def add_parser(self, **parsers):
        """Dynamically add parser to this DataStruct instance."""
        for n, p in parsers.items():
            if n in cls._field_parsers:
                m = "Conflicting parser found for the data structure field '%s'"
                raise FieldError(m % n)
            elif callable(p):
                cls._field_parsers[n] = p
            else:
                m = "The parser for the field '%s' is not callable"
                raise FieldError(m % n)

    def json(self, filepath=None, *args, **kwargs):
        """Encodes the struct as a json string which is returned, or writen to ``filepath``

        Parameters
        ----------
        filepath: str, None (default: None)
            The name of the file the json representation will be written to. If filepath
            is None, then the json representation is returned.
        *args, **kwargs: tuple, dict
            args and kwargs are encoding paramters for StructEncoder.__init__"""
        e = StructEncoder(*args, **kwargs)
        if filepath is None:
            return e.encode(self)
        else:
            with open(filepath, 'w') as f:
                f.write(e.encode(self))

    def __str__(self):
        return StructEncoder(sort_keys=True, indent=4, separators=(',', ': ')).encode(self)

    def __repr__(self):
        return StructEncoder().encode(self)

    def __eq__(self, other):
        if isinstance(other, DataStruct):
            return self._field_data == other._field_data
        else:
            return super(DataStruct, self).__eq__(other)
    

class LoadedDataStruct(DataStruct):

    def __init__(self, loader, *a, **kw):
        """Load, and map raw data onto the defined fields of this dict-like structure"""
        if isinstance(loader, lod.Loader):
            self._loader = loader
        elif issubclass(loader, lod.Loader):
            self._loader = loader(*a, **kw)
        else:
            loader_class = lod.Loader.__class__.__name__
            m = "Expected a subclass or instance of '%s' got: '%s' instead"
            raise ValueError(m % (loader_class, repr(loader)))

        super(LoadedDataStruct, self).__init__(self.read_from_loader())

    def read_from_loader(self):
        return self._loader.load()

# - - - - - - - - - - - - - - - - - - - -
# Data Structions From Predefined Loaders
# - - - - - - - - - - - - - - - - - - - -

class DataStructFromJSON(LoadedDataStruct):

    _loader = lod.JSONLoader

    def __init__(self, filename, path=None):
        l = self._loader(filename, path)
        super(DataStructFromJSON, self).__init__(l)

class DataStructFromCSV(LoadedDataStruct):

    _loader = lod.CSVLoader

    def __init__(self, filename, path=None, dialect='excel', **fmtparams):
        l = self._loader(filename, path, dialect, **fmtparams)
        super(DataStructFromCSV, self).__init__(l)
