#
# Copyright (C) 2011 - 2013 Red Hat, Inc.
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
import logging
import os.path


def _build_cmd(blabel, srpm):
    """
    Make up a command string to build given ``srpm``.

    NOTE: mock will print log messages to stderr (not stdout).

    >>> import logging
    >>> logging.getLogger().setLevel(logging.INFO)
    >>> _build_cmd("fedora-19-x86_64", "/tmp/abc-0.1.src.rpm")
    'mock -r fedora-19-x86_64 /tmp/abc-0.1.src.rpm'

    >>> logging.getLogger().setLevel(logging.DEBUG)
    >>> _build_cmd("fedora-19-x86_64", "/tmp/abc-0.1.src.rpm")
    'mock -r fedora-19-x86_64 /tmp/abc-0.1.src.rpm -v'

    :param blabel: Label of build target distribution,
        e.g. fedora-19-x86_64, fedora-custom-19-x86_64
    :return: A command string to build given ``srpm``
    """
    lvl = logging.getLogger().level
    c = "mock -r %s %s" % (blabel, srpm)

    # suppress log messages from mock by log level:
    if lvl >= logging.WARN:
        c += " > /dev/null 2> /dev/null"
    else:
        if lvl < logging.INFO:
            c += " -v"

    return c


class Distribution(object):
    """
    >>> d = Distribution("rhel", 6, "x86_64")
    >>> d.name, d.version, d.arch, d.bdist
    ('rhel', '6', 'x86_64', 'rhel-6')

    >>> d = Distribution("fedora", "19", "x86_64")
    >>> d.name, d.version, d.arch, d.bdist
    ('fedora', '19', 'x86_64', 'fedora-19')
    >>> d.label
    'fedora-19-x86_64'
    >>> d.label == d.blabel
    True
    >>> d.is_parent()
    True
    >>> d.base_mockcfg
    'fedora-19-x86_64.cfg'
    >>> d.base_mockcfg == d.mockcfg
    True

    >>> d = Distribution("fedora", "19", "x86_64", "fedora-custom-19")
    >>> d.name, d.version, d.arch, d.bdist
    ('fedora', '19', 'x86_64', 'fedora-custom-19')
    >>> d.blabel
    'fedora-custom-19-x86_64'
    >>> d.label == d.blabel
    False
    >>> d.base_mockcfg
    'fedora-19-x86_64.cfg'
    >>> d.mockcfg
    'fedora-custom-19-x86_64.cfg'
    """

    def __init__(self, name, version, arch, bdist=None):
        """
        :param name: Distribution name, e.g. "fedora", "rhel"
        :param version: Distribution version, e.g. "19" | 19, "6" | 6
        :param arch: Architecture, e.g. "i386", "x86_64"
        :param bdist: Build target distribution or None,
            e.g. "fedora-19", "fedora-custom-19".
        """
        self.name = name
        self.version = str(version)
        self.arch = arch

        self.dist = "%s-%s" % (name, version)
        self.label = "%s-%s-%s" % (name, version, arch)

        self.bdist = self.dist if bdist is None else bdist
        self.blabel = "%s-%s" % (self.bdist, arch)

        self.base_mockcfg = "%s.cfg" % self.label
        self.mockcfg = "%s.cfg" % self.blabel

    def rpmdir(self):
        """Dir to save built RPMs.
        """
        return "/var/lib/mock/%s/result" % self.blabel

    def build_cmd(self, srpm):
        return _build_cmd(self.blabel, srpm)

    def is_parent(self):
        return self.dist == self.bdist

# vim:sw=4:ts=4:et:
