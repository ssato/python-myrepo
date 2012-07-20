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


def _mk_modname(pyfile, prefix):
    """Make module name from path ($pyfile) and module prefix.

    >>> _mk_modname("/a/b/c.py", "a.b")
    'a.b.c'
    """
    return "%s.%s" % (prefix, os.path.basename(os.path.splitext(pyfile)[0]))


def find_plugin_modules(plugdir=None, prefix=PLUGINS_PREFIX,
        pattern=PLUGINS_FILENAME_PATTERN):
    """
    Scan $plugdir and return a list of plugin module names in that dir with
    prefixed $prefix.

    @param plugdir: Dir to search plugin modules
    @param prefix: Module name prefix
    """
    if not plugdir:
        plugdir = pluginsdir()

    return [
        _mk_modname(f, prefix) for f in
            sorted(glob.glob(os.path.join(plugdir, pattern)))
    ]


def import_plugin_modules(plugdir=None, prefix=PLUGINS_PREFIX,
        pattern=PLUGINS_FILENAME_PATTERN):
    """
    Effecful version of function to load plugin modules in plugdir.

    @return: [fully_qualified_plugin_module_name]

    NOTE: plugin modules are imported and visible in top level environment
    after called this.
    """
    ms = find_plugin_modules(plugdir, prefix, pattern)
    for m in ms:
        __import__(m)

    return ms


def _mname(pyfile):
    """
    >>> _mname("/a/b/c/d.py")
    'd'
    """
    return os.path.basename(os.path.splitext(pyfile)[0])


def _load_module(mname, mdir):
    """
    Load module $mname in $mdir and returns itself.
    """
    try:
        (fp, fn, stuff) = imp.find_module(mname, [mdir])
        return imp.load_module(m, fp, fn, stuff)
    except ImportError:
        logging.warn("Could not load module: name=%s, dir=%s" % (mname, mdir))
        return None
    finally:
        if fp:
            fp.close()


def load_plugin_modules(plugdir=None, pattern=PLUGINS_FILENAME_PATTERN):
    """
    Less effectful version of function to load plugin modules in plugdir.

    @return [(fully_qualified_plugin_module_name, plugin_module)]
    """
    if not plugdir:
        plugdir = pluginsdir()

    return [
        ("%s.%s" % (prefix, m), _load_module(m, plugdir)) for m in
            _mname(f) for f in
                sorted(glob.glob(os.path.join(plugdir, pattern)))
    ]


# vim:sw=4:ts=4:et:
