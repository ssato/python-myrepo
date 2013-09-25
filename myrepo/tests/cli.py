#
# Copyright (C) 2012, 2013 Red Hat, Inc.
# Red Hat Author(s): Satoru SATOH <ssato at redhat.com>
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
import myrepo.cli as TT
import myrepo.config as MC
import myrepo.repo as MR
import myrepo.tests.common as C

import itertools
import os.path
import os
import pprint
import shlex
import unittest


class Test_00_functions(unittest.TestCase):

    def test_10_mk_repos(self):
        ctx = MC._init_by_preset_defaults()
        repos = list(TT.mk_repos(ctx))

        ctx2 = ctx.copy()
        ctx2["dists"] = "fedora-19-x86_64,fedora-19-i386"

        expected = [MR.Repo("fedora", "19", ["x86_64", "i386"],
                            TT.mk_repo_server(ctx2),
                            ctx2["reponame"], selfref=ctx2["selfref"])]

        self.assertTrue(repos)
        self.assertEquals(len(repos), len(expected))

        f = pprint.pformat
        for r, e in itertools.izip_longest(repos, expected):
            self.assertEquals(r, e, C.diff(f(r), f(e)))


_CONF_0 = """[DEFAULT]
hostname: localhost
email: jdoe@example.com
name: fedora-com-example-jdoe
workdir: %(workdir)s
baseurl: file://%(workdir)s
dists: fedora-19-x86_64,fedora-19-i386,rhel-6-x86_64
"""

_LOCALHOST_CONF_0 = """\
[DEFAULT]
dists: fedora-19-x86_64,fedora-19-i386
hostname: localhost
altname: localhost
user: jdoe
baseurl: "file:///tmp"
reponame: "%%(name)s-%%(server_user)s"
fullname: Jone Doe
email: jdoe@localhost.localdomain

# The following parameters are substituted before writing this config to files:
workdir: %(workdir)s
topdir: %(topdir)s

# The following parameters are specified w/ corresponding options later:
#tpaths:
"""

_CURDIR = os.path.abspath(os.path.dirname(__file__))


class Test_10_modmain__localhost(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()
        self.conf = os.path.join(self.workdir, "00_localhost.conf")

        ctx = dict(workdir=self.workdir,
                   topdir=os.path.join(self.workdir, "yum"))

        open(self.conf, 'w').write(_LOCALHOST_CONF_0 % ctx)
        self.cfmt = "myrepo -v --config %s --tpaths %s %s %s"

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_10_init__w_no_genconf(self):
        """FIXME: How to do applicaiton tests under nosetests ?"""
        return
        c = self.cfmt % (self.conf, _CURDIR, "--no-genconf", "init")
        cs = shlex.split(c)

        self.assertEquals(TT.modmain(cs), 0)


# vim:sw=4:ts=4:et:
