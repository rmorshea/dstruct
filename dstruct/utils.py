"""Various utility functions"""

import os
import inspect
import six

def class_of(value):
    if inspect.isclass(value):
        return repr(value)
    else:
        t = type(value)
        return repr(t)

def repr_of(value):
    return "%r %r" % (value, type(value))

# Parts below taken from ipython:
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

def find_file(filename, path_dirs=None):
    """Find a file by looking through a sequence of paths.
    This iterates through a sequence of paths looking for a file and returns
    the full, absolute path of the first occurence of the file.  If no set of
    path dirs is given, the filename is tested as is, after running through
    :func:`expandvars` and :func:`expanduser`.  Thus a simple call::
        find_file('myfile.txt')
    will find the file in the current working dir, but::
        find_file('~/myfile.txt')
    Will find the file in the users home directory.  This function does not
    automatically try any paths, such as the cwd or the user's home directory.
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
    Raises :exc:`IOError` or returns absolute path to file.
    """

    # If paths are quoted, abspath gets confused, strip them...
    filename = filename.strip('"').strip("'")
    # If the input is an absolute path, just check it exists
    if os.path.isabs(filename) and os.path.isfile(filename):
        return filename

    if path_dirs is None:
        path_dirs = ("",)
    elif isinstance(path_dirs, six.string_types):
        path_dirs = (path_dirs,)

    for path in path_dirs:
        if path == '.': path = os.getcwd()
        testname = expand_path(os.path.join(path, filename))
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
