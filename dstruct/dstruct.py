
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

    dtype = None
    this_name = None
    this_class = None
    data_path = None

    def class_init(self, cls, name):
        self.this_class = cls
        self.this_name = name

    def install(self, cls):
        """Install this field object on the given ``cls``"""
        if self.data_path is not None:
            # assign to the flat field parser dict
            if self.this_name in cls._field_parsers:
                m = "Conflicting parser found for the data structure field '%s'"
                raise FieldError(m % self.this_name)
            else:
                cls._field_parsers[self.this_name] = self

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


    def __call__(self, inst, data):
        """Coerce ``data`` to the dtype of this field"""
        if self.dtype is not None:
            d = self.dtype(data)
        else:
            d = data
        return d

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
        value = self.__call__(inst, value)
        inst._field_data[self.this_name] = value


class DataField(BaseField):

    def __init__(self, dtype=None, *path):
        """Defines a field for data within a :class:`DataStruct`

        Parameters
        ----------
        dtype: class, function
            The type of data this field accepts, or a function for coersion. Values being
            assigned to this field are coerced to ``dtype(<value>)`` before being set.
            Errors encountered during coersion are allowed to raise.
        path: tuple
            The path to a value within a raw piece of data. If no path is provided
            the path is assumed to be ``(self.this_name)`` where ``self.this_name``
            is that of the attribute this field was defined under.
        """
        self.data_path = path or True
        if dtype is not None:
            self.dtype = dtype

    def class_init(self, cls, name):
        super(DataField, self).class_init(cls, name)
        if self.data_path is True:
            self.data_path = (self.this_name,)
        self.install(cls)
        


def datafield(dtype=None, *path, **kwargs):
    """A decorator defining a field and parser for data within a :class:`DataStruct`

    The handler passed to the decorator should be defined under the desired field
    name for the data structure. Handlers must accept one argument, that being the
    ``data`` which exists at the end of the given ``path``, and return the final
    value which will be assigned to the data structure.

    Parameters
    ----------
    dtype: class, function
        The type of data this field accepts, or a function for coersion. Values being
        assigned to this field are coerced via ``dtype(<value>)`` before being passed
        to the parser. Errors encountered during coersion are allowed to raise.
    path: tuple
        The path to a value within a raw piece of data. If no path is provided
        the path is assumed to be ``(self.this_name)`` where ``self.this_name``
        is that of the attribute this field was defined under.
    kwargs: dict
        By explicitely claiming ``path=None``, no assumptions are made about the
        ``path``, causing all the raw data to be passed to the handler for parsing.
    """
    return FieldParser(dtype, *path, **kwargs)


class FieldParser(BaseField):

    def __init__(self, dtype=None, *path, **kwargs):
        self.data_path = path or kwargs.get('path', True)
        if dtype is not None:
            self.dtype = dtype

    def _init_call(self, func):
        self.func = func
        return self

    def __call__(self, *args, **kwargs):
        if hasattr(self, 'func'):
            inst, value = args
            coerced = super(FieldParser, self).__call__(inst, value)
            return self.func(inst, coerced)
        else:
            return self._init_call(*args, **kwargs)

    def class_init(self, cls, name):
        super(FieldParser, self).class_init(cls, name)
        if self.data_path is True:
            self.data_path = (self.this_name,)
        elif self.data_path is None:
            self.data_path = ()
        self.install(cls)

# - - - - - - - - - - - - -
# Base Data Structure Class
# - - - - -- -- - - - - - -

class MetaStruct(type):

    def __init__(cls, name, bases, classdict):
        # the fields of the data structure
        # and their corresponding parsers
        cls._field_parsers = {}
        # paths within raw data that map to
        # the fields of the data structure
        cls._field_paths = {}

        super(MetaStruct, cls).__init__(name, bases, classdict)

        cdict = {}
        for c in cls.mro()[::-1]:
            cdict.update(c.__dict__)
        # install the fields of subclasses
        for k, v in cdict.items():
            if isinstance(v, BaseField):
                v.class_init(cls, k)


# use `utils.with_metaclass` for py3 compatibility
class DataStruct(utils.with_metaclass(MetaStruct, object)):

    def __new__(cls, data=None):
        inst = super(DataStruct, cls).__new__(cls)
        inst._field_data = {}
        return inst

    def __init__(self, data=None):
        """Map raw data onto the defined fields of this dict-like structure"""
        self.update(data)

    def __getitem__(self, field):
        return self._field_data[field]

    def __setitem__(self, field, data):
        if field in self._field_parsers:
            data = self._field_parsers[field](self, data)
        else:
            raise FieldError("No parser found for the field '%s'" % field)
        self._field_data[field] = data

    def __delitem__(self, field):
        p = self._field_parsers[field]

        d = self._field_paths
        if p.data_path is None:
            path = (p.this_name,)
        else:
            path = p.data_path

        for k in path:
            d = d[k]
        l = d[None]
        l.remove(p.this_name)

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
                self.__setitem__(field, value)

    def _map_data_to_fields(self, data):
        mapped = {}
        paths = self._field_paths
        val_iter = utils.parallel_dict_iter(paths, data)
        for path_value, data_value in val_iter:
            for field in path_value[None]:
                mapped[field] = data_value
        return mapped

    def add_fields(self, **fields):
        """Dynamically add fields to this DataStruct instance."""
        self.__class__ = type(self.__class__.__name__, (self.__class__,), fields)

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
