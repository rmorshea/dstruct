"""Various utility functions"""

import os
import inspect

def class_of(value):
    if inspect.isclass(value):
        return repr(value)
    else:
        t = type(value)
        return repr(t)

def repr_of(value):
    return "%r %r" % (value, type(value))

def parallel_dict_iter(d1, d2, stop=None):
    """Iterate over the common paths of two dicts yielding their respective values

    Parameters
    ----------
    d1, d2 : dict
        The two dicts whose values will be matched.
    stop: hashable
        if ``stop`` is found as a key in one of the nested dicts
        inside ``d1``, the current path location is yielded."""
    if isinstance(d1, dict) and isinstance(d2, dict):
        if stop in d1:
            yield d1, d2
        for k in (k for k in d1 if k in d2):
            for pair in parallel_dict_iter(d1[k], d2[k]):
                yield pair
    else:
        yield d1, d2

# Parts below taken from ipython:
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

def find_file(filename, path_dirs=None):
    """Find and load a json file by looking through a sequence of paths.

    Parameters
    ----------
    filename : str
        The filename to look for.
    path_dirs : str, None or sequence of str
        The sequence of paths to look for the file in.  If None, the filename
        need to be absolute or be in the cwd.  If a string, the string is
        put into a sequence and the searched.  If a sequence, walk through
        each element and join with ``filename``, calling :func:`expandvars`
        and :func:`expanduser` before testing for existence.
    
    Returns
    -------
    Raises :exc:`IOError` or returns the json file as a dict

    Notes
    -----
    See ``file_find`` for more info on how files are identified
    """
    # If paths are quoted, abspath gets confused, strip them...
    filename = filename.strip('"').strip("'")
    # If the input is an absolute path, just check it exists
    if os.path.isabs(filename) and os.path.isfile(filename):
        return filename

    if path_dirs is None:
        path_dirs = ("",)
    elif isinstance(path_dirs, (str, unicode)):
        path_dirs = (path_dirs,)

    for path in path_dirs:
        if path == '.':
            path = os.getcwd()
        joined = os.path.join(path, filename)
        testname = expand_path(joined)
        if os.path.isfile(testname):
            return os.path.abspath(testname)

    raise IOError("File %r does not exist in any of the search paths: %r" %
                  (filename, path_dirs) )


def expand_path(s):
    """Expand $VARS and ~names in a string, like a shell
    :Examples:
       In [2]: os.environ['FOO']='test'
       In [3]: expand_path('variable FOO is $FOO')
       Out[3]: 'variable FOO is test'
    """
    # This is a pretty subtle hack. When expand user is given a UNC path
    # on Windows (\\server\share$\%username%), os.path.expandvars, removes
    # the $ to get (\\server\share\%username%). I think it considered $
    # alone an empty var. But, we need the $ to remains there (it indicates
    # a hidden share).
    if os.name=='nt':
        s = s.replace('$\\', 'DSTRUCT_TEMP')
    s = os.path.expandvars(os.path.expanduser(s))
    if os.name=='nt':
        s = s.replace('DSTRUCT_TEMP', '$\\')
    return s

# Parts below taken from six:
# Copyright (c) 2010-2013 Benjamin Peterson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

def with_metaclass(meta, *bases):
    """Create a base class with a metaclass."""
    return meta("_NewBase", bases, {})
