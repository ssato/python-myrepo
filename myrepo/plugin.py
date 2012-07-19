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


# vim:sw=4:ts=4:et:
