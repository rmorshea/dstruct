"""A series of classes for loading external data"""

import csv
import json
from .utils import find_file

class Loader(object):
    """Base loader class for :class:`LoadedDataStruct`"""
    def __init__(*args, **kwargs): pass
    def load(self): pass


class FileLoader(Loader):

    filepath = None

    def __init__(self, filename, path=None):
        self.filepath = find_file(filename, path)

    def load(self):
        return self._read_file_as_dict()

    def _read_file_as_dict(self, filepath):
        pass


class JSONLoader(FileLoader):

    def _read_file_as_dict(self):
        with open(self.filepath) as f:
            d = json.load(f)
        return d

class CSVLoader(FileLoader):

    def __init__(self, filename, path=None, dialect='excel', **fmtparams):
        super(CSVLoader, self).__init__(filename, path)
        self.params = fmtparams
        self.dialect = dialect

    def _read_file_as_dict(self):
        with open(self.filepath) as f:
            reader = csv.reader(f, self.dialect, **self.params)
            d = TableMapping(list(reader))
        return d

# - - - - - - - - - - - - - - -
# Data Table Map For CSVLoader
# - - - - - - - - - - - - - - -

class TableMapping(dict):

    def __init__(self, list_of_lists=None):
        super(TableMapping, self).__init__()
        if list_of_lists is not None:
            self._encode_as_dict(list_of_lists)
            
    def _encode_as_dict(self, ll):
        for l in zip(*ll):
            if len(l) != len(set(l)):
                return self._narrowform_encoding(ll)
        else:
            return self._wideform_encoding(ll)

    def _wideform_encoding(self, ll):
        for i in range(1, len(ll)):
            d = {}
            l = ll[i]
            self[l[0]] = d
            for j in range(1, len(l)):
                d[ll[0][j]] = l[j]

    def _narrowform_encoding(self, ll):
        for l in ll[1:]:
            d = self
            for v in l[:-2]:
                if v in d:
                    d = d[v]
                else:
                    _d = {}
                    d[v] = _d
                    d = _d
            k, v = l[-2:]
            d[k] = v
