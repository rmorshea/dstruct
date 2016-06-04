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
        return self._read_file_as_dict(self.filepath)

    def _read_file_as_dict(self, filepath):
        pass


class JSONLoader(FileLoader):

    def _read_file_as_dict(self, filepath):
        with open(filepath) as f:
            d = json.load(f)
        return d

class CSVLoader(FileLoader):

    def __init__(self, filename, path=None, dialect='excel', table_form=None, **fmtparams):
        super(CSVLoader, self).__init__(filename, path)
        self.table_form = table_form
        self.params = fmtparams
        self.dialect = dialect

    def _read_file_as_dict(self, filepath):
        with open(filepath) as f:
            reader = csv.reader(f, self.dialect, **self.params)
            d = TableMapping(list(reader), self.table_form)
        return d

# - - - - - - - - - - - - - - -
# Data Table Map For CSVLoader
# - - - - - - - - - - - - - - -

class TableMapping(dict):

    def __init__(self, graph=None, encoding=None):
        """Convert a two dimensional categorical graph into a dict

        Parameters
        ----------
        graph: iterable of iterables
            The two dimensional object in a narrow or wide form encoding
        encoding: "wide" or "narrow" (default: None)
            Specify how the data graph is encoded. If not specified, the
            encoding is infered based on how categories are organized."""
        super(TableMapping, self).__init__()
        if graph is not None:
            if encoding == 'wide':
                self._wideform_encoding(graph)
            elif encoding == 'narrow':
                self._narrowform_encoding(graph)
            else:
                self.encode_as_dict(graph)
            
    def encode_as_dict(self, graph):
        for l in list(zip(*graph))[:-1]:
            # The first two columns are expected to
            # have shared categories. Thus duplicates
            # should be present.
            if len(l) != len(set(l)):
                return self._narrowform_encoding(graph)
        else:
            return self._wideform_encoding(graph)

    def _wideform_encoding(self, ll):
        for i in range(1, len(ll)):
            d = {}
            l = ll[i]
            try:
                self[l[0]] = d
            except IndexError:
                raise ValueError("No values in row 0")
            for j in range(1, len(l)):
                try:
                    v = l[j]
                except:
                    m = "No values in row %r, column %r"
                    raise ValueError(m % (i, j))
                else:
                    d[ll[0][j]] = v

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
