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
import myrepo.shell2 as SH

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


def _foreach_member_of(obj):
    for k, v in obj.__dict__.iteritems():
        if k.startswith('_') or callable(k):
            continue

        yield (k, v)


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

    >>> s.is_local
    False
    """

    def __init__(self, name, user, altname=None, topdir=G._SERVER_TOPDIR,
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
        self.timeout = timeout  # It will be ignored if this host is localhost.

        sep = '.'
        self.shortname = name.split(sep)[0] if sep in name else name

        ctx = dict(name=name, user=user, altname=self.altname, timeout=timeout,
                   shortname=self.shortname)

        # The followings may be format strings.
        self.topdir = _format(topdir, ctx)
        self.baseurl = _format(baseurl, ctx)

        self.is_local = SH.is_local(self.name)


class Repo(object):
    """
    Yum repository class.

    >>> server = RepoServer("yumrepos.local", "jdoe", "yumrepos.example.com")
    >>> repo = Repo("%(base_name)s-%(server_shortname)s-%(server_user)s",
    ...             19, ["x86_64", "i386"], "fedora", server)
    >>> repo.version, repo.archs, repo.base_name
    ('19', ['x86_64', 'i386'], 'fedora')
    >>> repo.server_name, repo.server_altname, repo.server_shortname
    ('yumrepos.local', 'yumrepos.example.com', 'yumrepos')
    >>> repo.server_baseurl
    'http://yumrepos.example.com/~jdoe/yum'
    >>> repo.multiarch, repo.primary_arch
    (True, 'x86_64')
    >>> repo.base_dist, repo.base_label
    ('fedora-19', 'fedora-19-x86_64')
    >>> repo.distdir, repo.destdir
    ('fedora/19', '~jdoe/public_html/yum/fedora/19')
    >>> repo.baseurl
    'http://yumrepos.example.com/~jdoe/yum/fedora/19'
    >>> repo.rpmdirs  # doctest: +NORMALIZE_WHITESPACE
    ['~jdoe/public_html/yum/fedora/19/sources',
     '~jdoe/public_html/yum/fedora/19/x86_64',
     '~jdoe/public_html/yum/fedora/19/i386']
    >>> repo.name, repo.dist, repo.label  # doctest: +NORMALIZE_WHITESPACE
    ('fedora-yumrepos-jdoe', 'fedora-yumrepos-jdoe-19',
     'fedora-yumrepos-jdoe-19-x86_64')
    >>> repo.repofile
    'fedora-yumrepos-jdoe-19.repo'
    """

    def __init__(self, name, version, archs, base_name, server,
                 bdist=None, subdir=G._SUBDIR,
                 signkey=G._SIGNKEY, keydir=G._KEYDIR, keyurl=G._KEYURL,
                 **kwargs):
        """
        :param name: Repository name or its format string,
            e.g. "rpmfusion-free", "rhel-custom" and
            "%(base_name)s-%(server_shortname)s-%(server_user)s".
        :param version: Version string or number :: int
        :param archs: List of architectures, e.g. ["x86_64", "i386"]

        :param base_name: Base (parent) distribution name
        :param server: RepoServer object :: myrepo.repo.RepoServer

        :param subdir: Dir or its format string to save RPMs of this repo,
            relative to the server's topdir.
        :param signkey: GPG key ID to sign, or None indicates will never sign
        ...
        """
        self.version = str(version)
        self.archs = archs
        self.base_name = base_name
        self.server = server
        self.keydir = keydir

        # TODO: Dirty hack.
        for k, v in _foreach_member_of(server):
            setattr(self, "server_" + k, v)

        self.multiarch = "i386" in self.archs and "x86_64" in self.archs
        self.primary_arch = "x86_64" if self.multiarch else self.archs[0]

        if self.multiarch:
            self.archs = [self.primary_arch] + \
                         [a for a in archs if a != self.primary_arch]

        self.base_dist = "%s-%s" % (base_name, self.version)
        self.base_label = "%s-%s" % (self.base_dist, self.primary_arch)

        if subdir is None:
            self.distdir = "%s/%s" % (base_name, self.version)
        else:
            self.distdir = self._format(subdir)

        self.destdir = os.path.join(self.server_topdir, self.distdir)
        self.baseurl = os.path.join(self.server_baseurl, self.distdir)

        self.rpmdirs = [os.path.join(self.destdir, d) for d in
                        ["sources"] + self.archs]

        self.name = self._format(name)

        self.dist = "%s-%s" % (self.name, self.version)

        if bdist is None:
            self.bdist = self.dist
        else:
            self.bdist = self._format(bdist)

        self.label = "%s-%s" % (self.dist, self.primary_arch)
        self.repofile = "%s.repo" % self.dist

        self.dists = [D.Dist(base_name, self.version, a, self.bdist)
                      for a in self.archs]

        if signkey is None:
            self.signkey = self.keyurl = self.keyfile = ""
        else:
            self.signkey = signkey
            self.keyurl = self._format(keyurl)
            self.keyfile = os.path.join(self.keydir,
                                        os.path.basename(self.keyurl))

    def _format(self, fmt_or_val):
        return _format(fmt_or_val, self.as_dict())

    def as_dict(self):
        return self.__dict__

# vim:sw=4:ts=4:et:
