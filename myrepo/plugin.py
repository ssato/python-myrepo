#
# Copyright (C) 2012 Red Hat, Inc.
# Red Hat Author(s): Masatake YAMATO <yamato@redhat.com>
# Red Hat Author(s): Satoru SATOH <ssato@redhat.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import glob
import imp
import logging
import os.path


PLUGINS_SUBDIR = "plugins"
PLUGINS_PREFIX = "myrepo.plugins"
PLUGINS_FILENAME_PATTERN = "[0-9]*.py*"


def selfdir():
    """
    Returns path where this module exists.
    """
    return os.path.dirname(__file__)


def pluginsdir(base=None, subdir=PLUGINS_SUBDIR):
    """
    Returns absolute path where plugin modules exist.
    """
    return os.path.join(base if base is not None else selfdir(), subdir)


def _mname(pyfile):
    """
    >>> _mname("/a/b/c/d.py")
    'd'
    """
    return os.path.basename(os.path.splitext(pyfile)[0])


def list_plugin_modules(plugdir=None, pattern=PLUGINS_FILENAME_PATTERN):
    """
    Scan $plugdir and return a list of module file names in that dir.

    @param plugdir: Dir to search module files
    @param pattern: Module file name pattern
    """
    if not plugdir:
        plugdir = pluginsdir()

    return [
        _mname(f) for f in sorted(glob.glob(os.path.join(plugdir, pattern)))
    ]


def import_plugin_modules(plugdir=None, prefix=PLUGINS_PREFIX,
        pattern=PLUGINS_FILENAME_PATTERN):
    """
    Effecful version of function to load modules in plugdir.

    @return: [fully_qualified_plugin_module_name]

    NOTE: plugin modules are imported and visible in top level environment
    after called this.
    """
    ms = [
        "%s.%s" % (prefix, m) for m in
            list_plugin_modules(plugdir, prefix, pattern)
    ]
    for m in ms:
        __import__(m)

    return ms


def _load_module(mname, mdir):
    """
    Load module $mname in $mdir and returns itself.
    """
    fp = None
    try:
        (fp, fn, stuff) = imp.find_module(mname, [mdir])
        return imp.load_module(mname, fp, fn, stuff)
    except ImportError:
        logging.warn("Could not load module: name=%s, dir=%s" % (mname, mdir))
    finally:
        if fp:
            fp.close()

    return None


def load_plugin_modules(plugdir=None, pattern=PLUGINS_FILENAME_PATTERN):
    """
    Less effectful version of function to load plugin modules in plugdir.

    @return [plugin_module]
    """
    if not plugdir:
        plugdir = pluginsdir()

    return [
        _load_module(m, plugdir) for m in
            list_plugin_modules(plugdir, pattern)
    ]


# vim:sw=4:ts=4:et:
