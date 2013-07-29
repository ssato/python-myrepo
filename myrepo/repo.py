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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
from operator import attrgetter

import myrepo.distribution as D
import myrepo.globals as G

import os.path


def _format(fmt_or_val, ctx={}):
    """
    (Format Str | Str) -> Str

    >>> _format("aaa", {})
    'aaa'
    >>> _format("%(a)s", dict(a="123", ))
    '123'

    :param ctx: Context dict object for format strings
    """
    return fmt_or_val % ctx if "%" in fmt_or_val else fmt_or_val


class Repo(object):
    """
    Yum repository class.
    """
    name = G.REPO_DEFAULT["name"]
    subdir = G.REPO_DEFAULT["subdir"]
    topdir = G.REPO_DEFAULT["topdir"]
    baseurl = G.REPO_DEFAULT["baseurl"]

    signkey = G.REPO_DEFAULT["signkey"]
    keydir = G.REPO_DEFAULT["keydir"]
    keyurl = G.REPO_DEFAULT["keyurl"]

    timeout = G.REPO_DEFAULT["conn_timeout"]
    metadata_expire = G.REPO_DEFAULT["metadata_expire"]

    def __init__(self, server, user, dname, dver, archs=None,
                 name=None, subdir=None, topdir=None, baseurl=None,
                 signkey=None, bdist=None, timeout=None, **kwargs):
        """
        :param server: Server's hostname to provide this yum repo
        :param user: Username on the server
        :param dname: Distribution name, e.g. "fedora", "rhel"
        :param dver: Distribution version, e.g. "16", "6"
        :param archs: Architecture list, e.g. ["i386", "x86_64"]
        :param name: Repository name or its format string,
            e.g. "rpmfusion-free", "%(distname)s-%(hostname)s-%(user)s"
        :param subdir: Sub directory for this repository
        :param topdir: Topdir or its format string for this repository,
            e.g. "/var/www/html/%(subdir)s".
        :param baseurl: Base url or its format string, e.g.
            "file://%(topdir)s".
        :param signkey: GPG key ID to sign, or None indicates will never sign
        :param bdist: Distribution label to build srpms,
            e.g. "fedora-custom-addons-14-x86_64"
        :param timeout: Command execution timeout in seconds or None
        """
        self.server = server
        self.user = user
        self.archs = archs

        self.hostname = server.split('.')[0]
        self.multiarch = "i386" in self.archs and "x86_64" in self.archs
        self.primary_arch = "x86_64" if self.multiarch else self.archs[0]

        if self.multiarch:
            self.archs = [self.primary_arch] + \
                         [a for a in archs if a != self.primary_arch]

        self.distname = dname
        self.distversion = dver
        self.dist = "%s-%s" % (dname, dver)

        self.dists = [D.Distribution(dname, dver, a, bdist) for a in
                      self.archs]
        self.distdir = "%s/%s" % (dname, dver)
        self.subdir = self.subdir if subdir is None else subdir

        if name is None:
            name = Repo.name

        if topdir is None:
            topdir = Repo.topdir

        if baseurl is None:
            baseurl = Repo.baseurl

        if bdist is None:
            bdist = "%s-%s-%s" % (name, self.distversion, self.primary_arch)

        self.bdist = bdist

        if timeout is not None:
            self.timeout = timeout

        # expand parameters which are format strings:
        self.name = self._format(name)
        self.topdir = self._format(topdir)
        self.baseurl = self._format(baseurl)

        self.keydir = Repo.keydir

        if signkey is None:
            self.signkey = self.keyurl = self.keyfile = ""
        else:
            self.signkey = signkey
            self.keyurl = self._format(Repo.keyurl)
            self.keyfile = os.path.join(self.keydir,
                                        os.path.basename(self.keyurl))

    def _format(self, fmt_or_val):
        return _format(fmt_or_val, self.as_dict())

    def as_dict(self):
        return self.__dict__.copy()

    def destdir(self):
        return os.path.join(self.topdir, self.distdir)

    def rpmdirs(self):
        return [os.path.join(self.destdir(), d) for d in
                ["sources"] + self.archs]

# vim:sw=4:ts=4:et:
