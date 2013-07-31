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


class RepoServer(object):
    """
    >>> s = RepoServer("localhost", "jdoe",
    ...                baseurl="file:///home/%(user)s/public_html/yum")
    >>> s.name, s.user, s.altname, s.shortname
    ('localhost', 'jdoe', 'localhost', 'localhost')
    >>> s.topdir
    '~jdoe/public_html/yum'
    >>> s.baseurl
    'file:///home/jdoe/public_html/yum'

    >>> s = RepoServer("yumrepos.local", "jdoe", "yumrepos.example.com")
    >>> s.name, s.user, s.altname, s.shortname
    ('yumrepos.local', 'jdoe', 'yumrepos.example.com', 'yumrepos')
    >>> s.baseurl
    'http://yumrepos.example.com/~jdoe/yum'
    """

    def __init__(self, name, user, altname=None, topdir=G._TOPDIR,
                 baseurl=G._SERVER_BASEURL, timeout=G._CONN_TIMEOUT):
        """
        :param name: FQDN or hostname of the server provides yum repos
        :param user: User name on the server to provide yum repos
        :param altname: Alternative hostname (FQDN) for client access
        :param topdir: Top dir or its format string of yum repos to serve RPMs.
        :param baseurl: Base url or its format string of yum repos
        :param timeout: SSH connection timeout to this server
        """
        self.name = name
        self.user = user
        self.altname = name if altname is None else altname
        self.timeout = timeout

        sep = '.'
        self.shortname = name.split(sep)[0] if sep in name else name

        ctx = dict(name=name, user=user, altname=self.altname, timeout=timeout,
                   shortname=self.shortname)

        # The followings may be format strings.
        self.topdir = _format(topdir, ctx)
        self.baseurl = _format(baseurl, ctx)


class Repo(object):
    """
    Yum repository class.
    """
    name = G.REPO_DEFAULT["name"]
    topdir = G.REPO_DEFAULT["topdir"]
    baseurl = G.REPO_DEFAULT["baseurl"]

    signkey = G.REPO_DEFAULT["signkey"]
    keydir = G.REPO_DEFAULT["keydir"]
    keyurl = G.REPO_DEFAULT["keyurl"]

    metadata_expire = G.REPO_DEFAULT["metadata_expire"]

    def __init__(self, server, user, dname, dver, archs=None,
                 name=None, topdir=None, baseurl=None,
                 signkey=None, bdist=None):
        """
        :param server: Server's hostname to provide this yum repo
        :param user: Username on the server
        :param dname: Distribution name, e.g. "fedora", "rhel"
        :param dver: Distribution version, e.g. "16", "6"
        :param archs: Architecture list, e.g. ["i386", "x86_64"]
        :param name: Repository name or its format string,
            e.g. "rpmfusion-free", "%(distname)s-%(hostname)s-%(user)s"
        :param topdir: Topdir or its format string for this repository,
        :param baseurl: Base url or its format string, e.g.
            "file://%(topdir)s".
        :param signkey: GPG key ID to sign, or None indicates will never sign
        :param bdist: Distribution label to build srpms,
            e.g. "fedora-custom-addons-14-x86_64"
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

        if name is None:
            name = Repo.name

        if topdir is None:
            topdir = Repo.topdir

        if baseurl is None:
            baseurl = Repo.baseurl

        if bdist is None:
            bdist = "%s-%s-%s" % (name, self.distversion, self.primary_arch)

        self.bdist = bdist

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

        self.destdir = os.path.join(self.topdir, self.distdir)
        self.rpmdirs = [os.path.join(self.destdir, d) for d in
                        ["sources"] + self.archs]

        self.repofile = "%s.repo" % self.name

    def _format(self, fmt_or_val):
        return _format(fmt_or_val, self.as_dict())

    def as_dict(self):
        return self.__dict__.copy()

# vim:sw=4:ts=4:et:
