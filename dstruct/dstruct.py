import six
import json
from inspect import getmembers
import types

from .loader import Loader, FileLoader, JSONLoader, CSVLoader

# - - - - -
# Utilities
# - - - - -

class FieldError(Exception): pass

class StructEncoder(json.JSONEncoder):
    def default(self, obj):
        if not isinstance(obj, DataStruct):
            raise ValueError("Expected a DataStruct obj, not %r" % obj)
        else:
            return obj._field_values.copy()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Base Descriptor Protocol (inspired by IPython's Traitlets)
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class BaseDescriptor(object):

    info = 'base descriptor'
    this_class = None
    this_name = None

    def init_self(self, cls, name):
        """Initialize this descriptor instance

        Parameters
        ----------
        cls : class
            The class which owns this descriptor
        name : str
            The attribute name of this descriptor
        """
        # the class the descriptor is defined on
        self.this_class = cls
        # the attribute name of this descriptor
        self.this_name = name

    def init_cls(self, cls):
        """Initialize this descriptor as a class member

        Parameters
        ----------
        cls : class
            A class which this descriptor is a member of
        """
        pass

    def init_inst(self, inst):
        """Initialize this descriptor for an instance

        Parameters
        ----------
        inst : instance
            An instance dependant on this descriptor
        """
        pass

    def __repr__(self):
        if None in (self.this_name, self.this_class):
            return '<unbound base descriptor'
        else:
            return '<%s %s.%s>' % (self.info, self.this_class.__name__, self.this_name)


class MetaHasDescriptors(type):

    def __init__(cls, name, bases, classdict):
        cls.setup_class(classdict)

    def setup_class(cls, classdict):
        # initialize struct member on
        # the class which owns them
        for k, v in classdict.items():
            if isinstance(v, BaseDescriptor):
                v.init_self(cls, k)
        # initialize the class which has
        # these struct members in its mro
        for k, v in getmembers(cls):
            if isinstance(v, BaseDescriptor):
                v.init_cls(cls)


class HasDescriptors(six.with_metaclass(MetaHasDescriptors, object)):

    def __new__(cls, *args, **kwargs):
        new = super(HasDescriptors, cls).__new__
        if new is object.__new__:
            inst = new(cls)
        else:
            inst = new(cls, *args, **kwargs)
        inst.setup_self(*args, **kwargs)
        return inst

    def setup_self(self, *args, **kwargs):
        for k, v in getmembers(self.__class__):
            if isinstance(v, BaseDescriptor):
                v.init_inst(self)

# - - - - - - - - - - - - - - - - -
# Data Structures and Field Members
# - - - - - - - - - - - - - - - - -


class dataparser(BaseDescriptor):

    _func = None
    info = 'data parser'

    def __init__(self, *names, **kwargs):
        """A decorator that creates parsers for the fields of a data structure

        Parameters
        ----------
        *names:
            The field names this parser should be applied to
        **kwargs:
            Keyword arguments do not affect decorator logic. If this instance is not
            a decorator, then specify a parser with the keyword ``func=<callable>`` and
            whether it should be treated as a method type with ``method_type=<bool>``
            (default: False).

        Parsers accept one argument for raw values and return a parsed value.
        """
        self.names = names or None
        f = kwargs.get('func')
        b = kwargs.get('method_type', False)
        if not isinstance(b, bool):
            raise ValueError("The 'method_type' keyword must be a 'bool'")
        if f is not None:
            self._setup_parser(f, b)

    def __call__(self, *args, **kwargs):
        """Specify a method type parser"""
        if self._func is not None:
            return self._func(*args, **kwargs)
        else:
            self._setup_parser(*args, method_type=True)
            return self

    def _setup_parser(self, func, method_type):
        if callable(func):
            if method_type and not isinstance(func, types.FunctionType):
                m = "Decorator cannot coerce %r to method type"
                raise ValueError(m % func)
            self._func = func
        else:
            raise ValueError("Parser must be callable")
        self.method_type = method_type 

    def init_self(self, cls, name):
        super(dataparser, self).init_self(cls, name)
        for name in self.names:
            # allow getattr to raise
            field = getattr(cls, name)
            if isinstance(field, DataField):
                if name in cls.__dict__ and field.parser is not None:
                    m = "Conflicting parsers for the field '%s'"
                    raise FieldError(m % name)
            else:
                m = "The name '%s' is not a field of a '%s'"
                raise FieldError(m % (name, cls.__name__))
        if self.this_name in cls._field_parsers:
            m = "Conflicting parsers for the field '%s'"
            raise FieldError(m % name)
        else:
            for n in self.names:
                cls._field_parsers[n] = self

    def get(self, inst=None, cls=None):
        if self.method_type:
            return types.MethodType(self._func, inst)
        else:
            return self._func

    def __get__(self, inst, cls=None):
        if inst is None:
            return self
        else:
            return self.get(inst, cls)

class DataField(BaseDescriptor):

    parser = None
    info = 'data field'

    def __init__(self, *path, **kwargs):
        """Defines a field for data within a :class:`DataStruct`

        Parameters
        ----------
        path: tuple
            The path to the value of this field in a data set. If no path is provided
            the path is assumed to be ``(self.this_name,)`` where ``self.this_name``
            is the name of the attribute this field was defined under.
        **kwargs:
            By explicitely claiming ``path=None``, no assumptions are made about the
            ``path`` meaning the whole data set is set as the value of this field.
            Asserting ``parser=<callable>`` creates a parser for this data field.
            Parser functions accept one argument for the raw value being set on the
            field, and return a parsed value.
        """
        self.path = path or kwargs.get('path', True)
        f = kwargs.get('parser')
        if f is not None:
            self.setup_parser(f)

    def __call__(self, func):
        """Sets up a function as a `dataparser`"""
        # parser is setup as a method type
        p = dataparser(func=func, method_type=True)
        self.setup_parser(p)
        return self

    def setup_parser(self, parser):
        if self.parser is None:
            if not isinstance(parser, dataparser):
                # parser is not setup as a method type
                self.parser = dataparser(func=parser)
            else:
                self.parser = parser
        else:
            m = "The field '%s' already has a parser"
            raise FieldError(m % self.this_name)

    def init_self(self, cls, name):
        super(DataField, self).init_self(cls, name)
        if self.path is True:
            self.path = (self.this_name,)
        if self.path is None:
            self.path = ()
        cls._field_paths[self.this_name] = self.path
        if self.parser is not None:
            cls._field_parsers[self.this_name] = self.parser

    def get(self, inst):
        try:
            return inst._field_values[self.this_name]
        except KeyError:
            m = "The field '%s' has no data"
            raise FieldError(m % self.this_name)

    def __get__(self, inst, cls=None):
        if inst is not None:
            return self.get(inst)
        else:
            return self

    def set(self, inst, value):
        inst._field_values[self.this_name] = value

    def parse_value(self, inst, value):
        if self.this_name in inst._field_parsers:
            p = inst._field_parsers[self.this_name]
            if p.method_type:
                value = p(inst, value)
            else:
                value = p(value)
        return value

    def __set__(self, inst, value):
        self.set(inst, self.parse_value(inst, value))


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
    if len(path) == 1 and isinstance(path[0], types.FunctionType):
        return DataField(**kwargs)(*path)
    else:
        return DataField(*path, **kwargs)


class MetaStruct(MetaHasDescriptors):

    def setup_class(cls, classdict):
        cls._field_paths = {}
        cls._field_parsers = {}
        super(MetaStruct, cls).setup_class(classdict)
        temp_paths = {}
        temp_parsers = {}
        for c in cls.mro()[::-1]:
            if issubclass(c.__class__, MetaStruct):
                temp_paths.update(c._field_paths)
                temp_parsers.update(c._field_parsers)
        cls._field_paths = temp_paths
        cls._field_parsers = temp_parsers


class DataStruct(six.with_metaclass(MetaStruct, HasDescriptors)):

    def setup_self(self, *args, **kwargs):
        self._field_values = {}
        super(DataStruct, self).setup_self(*args, **kwargs)

    def __init__(self, data=None):
        self.update(data)

    def __getitem__(self, name):
        f = getattr(self, name, None)
        if isinstance(f, DataField):
            return f.__get__(self)
        else:
            raise FieldError("No field named '%s'" % name)

    def __setitem__(self, name, value):
        f = getattr(self, name, None)
        if isinstance(f, DataField):
            f.__set__(self, value)
        else:
            raise FieldError("No field named '%s'" % name)

    def update(self, data=None):
        if data is not None:
            for f, p in self._field_paths.items():
                _data = data
                for k in p:
                    if isinstance(_data, dict) and k in _data:
                        _data = _data[k]
                    else:
                        break
                else:
                    setattr(self, f, _data)

    @classmethod
    def has_field(cls, name):
        return isinstance(getattr(cls, name, None), DataField)

    @classmethod
    def class_owned_fields(cls):
        return {k:v for k, v in cls.__dict__.items() if isinstance(v, DataField)}

    @classmethod
    def fields(cls):
        return {k:v for k, v in getmembers(cls) if isinstance(v, DataField)}

    def add_fields(self, **fields):
        """Add new data fields to this struct instance"""
        self.__class__ = type(self.__class__.__name__,
                            (self.__class__,), fields)
        for k, v in fields.items():
            v.init_inst(self)

    def del_fields(self, *names):
        """Delete data fields from this struct instance"""
        cls = type(self)
        self.__class__ = cls
        for n in names:
            # don't raise error if a field is absent
            if isinstance(getattr(cls, n, None), DataField):
                if n in self._field_values:
                    del self._field_values[n]
                delattr(cls, n)

    def set_field(self, name, value):
        """Forcibly sets field values without parsing"""
        f = getattr(self, name, None)
        if isinstance(f, DataField):
            f.set(self, value)
        else:
            raise FieldError("No field named '%s'" % name)

    @classmethod
    def class_owned_parsers(cls):
        d = {}
        # assumes no conflicts exist
        for k, v in cls.__dict__.items():
            if isinstance(v, dataparser):
                d[k] = v
            elif isinstance(v, DataField) and v.parser is not None:
                d[k] = v.parser
        return d

    @classmethod
    def parsers(cls):
        d = {}
        # assumes no conflicts exist
        for k, v in getmembers(cls):
            if isinstance(v, dataparser):
                d[k] = v
            elif isinstance(v, DataField) and v.parser is not None:
                d[k] = v.parser
        return d

    def __iter__(self):
        return iter(self._field_values)

    def __str__(self):
        return StructEncoder(sort_keys=True, indent=4, separators=(',', ': ')).encode(self)

    def __repr__(self):
        return StructEncoder().encode(self)

    def __eq__(self, other):
        if isinstance(other, DataStruct):
            return self._field_values == other._field_values
        else:
            return self._field_values == other


class LoadedDataStruct(DataStruct):

    def __init__(self, loader, *a, **kw):
        """Load, and map raw data onto the defined fields of this dict-like structure"""
        if isinstance(loader, Loader):
            self._loader = loader
        elif issubclass(loader, Loader):
            self._loader = loader(*a, **kw)
        else:
            loader_class = Loader.__class__.__name__
            m = "Expected a subclass or instance of '%s' got: '%s' instead"
            raise ValueError(m % (loader_class, repr(loader)))

        super(LoadedDataStruct, self).__init__(self.read_from_loader())

    def read_from_loader(self):
        return self._loader.load()

# - - - - - - - - - - - - - - - - - - - -
# Data Structions From Predefined Loaders
# - - - - - - - - - - - - - - - - - - - -

class DataStructFromJSON(LoadedDataStruct):

    _loader = JSONLoader

    def __init__(self, filename, path=None):
        l = self._loader(filename, path)
        super(DataStructFromJSON, self).__init__(l)

class DataStructFromCSV(LoadedDataStruct):

    _loader = CSVLoader

    def __init__(self, filename, path=None, dialect='excel', **fmtparams):
        l = self._loader(filename, path, dialect, **fmtparams)
        super(DataStructFromCSV, self).__init__(l)
