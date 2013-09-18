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
import myrepo.globals as G
import myrepo.srpm as MS
import myrepo.shell as SH
import myrepo.utils as U
import rpmkit.rpmutils as RU
import rpmkit.environ as E

import glob
import locale
import logging
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


# Classes:
class Server(object):
    """
    >>> s = Server("localhost", "jdoe",
    ...                baseurl="file:///home/%(user)s/public_html/yum")
    >>> s.name, s.user, s.altname, s.shortname, s.shortaltname
    ('localhost', 'jdoe', 'localhost', 'localhost', 'localhost')
    >>> s.topdir
    '~jdoe/public_html/yum'
    >>> s.baseurl
    'file:///home/jdoe/public_html/yum'

    >>> s = Server("yumrepos.local", "jdoe", "yumrepos.example.com")
    >>> s.name, s.user, s.altname, s.shortname, s.shortaltname
    ('yumrepos.local', 'jdoe', 'yumrepos.example.com', 'yumrepos', 'yumrepos')
    >>> s.baseurl
    'http://yumrepos.example.com/~jdoe/yum'

    >>> s.is_local
    False

    >>> s = Server("localhost", "jdoe", baseurl="file:///tmp")
    >>> s.baseurl
    'file:///tmp'
    >>> s.is_local
    True
    """

    def __init__(self, name, user=None, altname=None, topdir=G._SERVER_TOPDIR,
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
        self.user = E.get_username() if user is None else user
        self.altname = name if altname is None else altname
        self.timeout = timeout  # It will be ignored if this host is localhost.

        self.shortname = self._mk_shortname(self.name)
        self.shortaltname = self._mk_shortname(self.altname)

        ctx = dict(name=name, user=self.user, altname=self.altname,
                   timeout=timeout, shortname=self.shortname,
                   shortaltname=self.shortaltname)

        # The followings may be format strings.
        self.topdir = _format(topdir, ctx)
        self.baseurl = _format(baseurl, ctx)

        self.is_local = SH.is_local(self.name)

    def _mk_shortname(self, name, sep='.'):
        return name.split(sep)[0] if sep in name else name

    def adjust_cmd(self, cmd, workdir=os.curdir):
        """
        :param cmd: Command string
        :param workdir: Working directory in which command runs

        :return: A tuple of (command_string, workdir)
        """
        return SH.adjust_cmd(cmd, self.user, self.name, workdir)

    def deploy_cmd(self, src, dst):
        """
        Make up and and return command strings to deploy objects from ``src``
        to ``dst`` on the server.

        :param src: Copying source (path) :: str
        :param dst: Copying destination (path) :: str

        :return: command string to deploy objects :: str
        """
        if self.is_local:
            if "~" in dst:
                dst = os.path.expanduser(dst)

            return "cp -a %s %s" % (src, dst)
        else:
            h = "%s@%s" % (self.user, self.name) if self.user else self.name
            return "scp -p %s %s:%s" % (src, h, dst)


class Dist(object):
    """
    >>> d = Dist("fedora-19", "x86_64")
    >>> d.dist, d.arch, d.label
    ('fedora-19', 'x86_64', 'fedora-19-x86_64')
    >>> d.mockcfg
    'fedora-19-x86_64.cfg'
    """

    def __init__(self, dist, arch):
        """
        :param dist: ${name}-${version}, e.g. "fedora-19", "rhel-6".
        :param arch: Architecture, e.g. "i386", "x86_64"
        """
        self.dist = dist
        self.arch = arch

        self.label = "%s-%s" % (dist, arch)
        self.mockcfg = "%s.cfg" % self.label

    def rpmdir(self):
        """Dir to save built RPMs.
        """
        return "/var/lib/mock/%s/result" % self.label


class MaybeMultiarchDist(object):
    """
    A collection of Dist objects having same name and same version but
    different architectures.

    >>> d = MaybeMultiarchDist("fedora", 19, ["x86_64", "i386"])
    >>> d.name, d.version, d.dist, d.subdir
    ('fedora', '19', 'fedora-19', 'fedora/19')
    >>> d.multiarch, d.primary_arch
    (True, 'x86_64')

    >>> d = MaybeMultiarchDist("fedora", 19, ["x86_64"])
    >>> d.multiarch, d.primary_arch
    (False, 'x86_64')
    """

    def __init__(self, name, version, archs, primary_arch="x86_64"):
        """
        :param name: Distribution name, fedora or rhel.
        :param version: Version string or number :: int
        :param archs: List of architectures, e.g. ["x86_64", "i386"]
        :param primary_arch: Primary arch or None. If archs[0] is the
            primary_arch, pass None as this.
        """
        assert archs, "parameter 'archs' must not be an empty list!"
        assert all(a in G._RPM_ARCHS for a in archs), \
            "Invalid arch[s] found in given arch list: " + ', '.join(archs)

        self.name = name
        self.version = str(version)
        self.dist = "%s-%s" % (self.name, self.version)
        self.subdir = os.path.join(self.name, self.version)
        self.multiarch = len(archs) > 1

        if primary_arch in archs:
            self.primary_arch = primary_arch
            self.other_archs = [a for a in archs if a != primary_arch]
            self.archs = [self.primary_arch] + self.other_archs
        else:
            self.primary_arch = archs[0]
            self.other_archs = archs[1:]
            self.archs = archs

        self.labels = ["%s-%s" % (self.dist, a) for a in self.archs]


class Repo(object):
    """
    Yum repository.

    >>> s = Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
    >>> repo = Repo("fedora", 19, ["x86_64", "i386"], s,
    ...             reponame="%(name)s-%(server_shortaltname)s")
    >>> repo.name, repo.version, repo.archs, repo.other_archs
    ('fedora', '19', ['x86_64', 'i386'], ['i386'])
    >>> repo.server_name, repo.server_altname
    ('yumrepos-1.local', 'yumrepos.example.com')
    >>> repo.server_shortname, repo.server_shortaltname,
    ('yumrepos-1', 'yumrepos')
    >>> repo.server_baseurl
    'http://yumrepos.example.com/~jdoe/yum'
    >>> repo.multiarch, repo.primary_arch
    (True, 'x86_64')
    >>> repo.subdir, repo.destdir
    ('fedora/19', '~jdoe/public_html/yum/fedora/19')
    >>> repo.baseurl
    'http://yumrepos.example.com/~jdoe/yum'
    >>> repo.url
    'http://yumrepos.example.com/~jdoe/yum/fedora/19'
    >>> repo.rpmdirs  # doctest: +NORMALIZE_WHITESPACE
    ['~jdoe/public_html/yum/fedora/19/sources',
     '~jdoe/public_html/yum/fedora/19/x86_64',
     '~jdoe/public_html/yum/fedora/19/i386']
    >>> repo.reponame
    'fedora-yumrepos'

    >>> srpm = MS.Srpm("/dummy/path/src.rpm"); srpm.noarch = False
    >>> repo.list_build_labels(srpm)
    ['fedora-19-x86_64', 'fedora-19-i386']
    >>> repo.mockcfg_files(srpm)
    ['fedora-19-x86_64.cfg', 'fedora-19-i386.cfg']
    >>> repo.mockdirs(srpm)  # doctest: +NORMALIZE_WHITESPACE
    ['/var/lib/mock/fedora-19-x86_64/result',
     '/var/lib/mock/fedora-19-i386/result']
    """

    def __init__(self, name, version, archs, server, reponame=G._REPONAME,
                 primary_arch="x86_64", build_for_self=False):
        """
        :param name: Build target distribution name, fedora or rhel.
        :param version: Version string or number :: int
        :param archs: List of architectures, e.g. ["x86_64", "i386"]
        :param server: Server object :: myrepo.repo.Server
        :param reponame: This repo's name or its format string, e.g.
            "fedora-custom", "%(name)s-%(server_shortaltname)s"
        :param primary_arch: Primary arch or None. If archs[0] is the
            primary_arch, pass None as this.
        :param build_for_self: build given srpm for self if True
        """
        self.name = name
        self.version = str(version)
        self.server = server
        self.multiarch = len(archs) > 1
        self.build_for_self = build_for_self

        # Setup aliases of self.server.<key>:
        for k, v in _foreach_member_of(server):
            setattr(self, "server_" + k, v)

        if primary_arch in archs:
            self.primary_arch = primary_arch
            self.other_archs = [a for a in archs if a != primary_arch]
        else:
            self.primary_arch = archs[0]
            self.other_archs = archs[1:]

        self.archs = [self.primary_arch] + self.other_archs

        self.subdir = os.path.normpath(os.path.join(self.name, self.version))
        self.destdir = os.path.normpath(os.path.join(self.server_topdir,
                                                     self.subdir))
        self.baseurl = self.server_baseurl
        self.url = os.path.join(self.baseurl, self.subdir)

        self.rpmdirs = [os.path.join(self.destdir, d) for d in
                        ["sources"] + self.archs]

        self.reponame = self._format(reponame)

        self.dist = "%s-%s" % (self.reponame if self.build_for_self else
                               self.name, self.version)
        self.dists = [Dist(self.dist, a) for a in self.archs]
        self.primary_dist = self.dists[0]

    def as_dict(self):
        return self.__dict__

    def _format(self, fmt_or_val):
        return _format(fmt_or_val, self.as_dict())

    def list_dists(self, srpm):
        """
        Return mock.cfg files to build given ``sprm``.

        :param srpm: "resolved" myrepo.srpm.Srpm instance
        :return: List of paths to mock.cfg files
        """
        return [self.primary_dist] if srpm.noarch else self.dists

    def list_build_labels(self, srpm):
        """
        Return list of build lables for given srpm.

        :param srpm: "resolved" myrepo.srpm.Srpm instance
        :return: List of paths to mock.cfg files
        """
        return [d.label for d in self.list_dists(srpm)]

    def mockcfg_files(self, srpm):
        """
        Return mock.cfg files to build given ``sprm``.

        :param srpm: "resolved" myrepo.srpm.Srpm instance
        :return: List of paths to mock.cfg files
        """
        return [d.mockcfg for d in self.list_dists(srpm)]

    def mockdirs(self, srpm):
        """
        Return dirs where built RPMs are.

        :param srpm: "resolved" myrepo.srpm.Srpm instance
        :return: List of paths to dirs in which built RPMs are
        """
        return [d.rpmdir() for d in self.list_dists(srpm)]

    def adjust_cmd(self, cmd, workdir=os.curdir):
        """
        :param cmd: Command string
        :param workdir: Working directory in which command runs

        :return: A tuple of (command_string, workdir)
        """
        return self.server.adjust_cmd(cmd, workdir)

    def mk_cmd(self, cmd, workdir=os.curdir):
        """
        Alias to self.adjust_cmd.
        """
        return self.adjust_cmd(cmd, workdir)

    def deploy_cmd(self, src, dst):
        """
        Make up and and return command strings to deploy objects from ``src``
        to ``dst`` on the server.

        :param src: Copying source (path) :: str
        :param dst: Copying destination (path) :: str

        :return: command string to deploy objects :: str
        """
        return self.server.deploy_cmd(src, dst)

# vim:sw=4:ts=4:et:
