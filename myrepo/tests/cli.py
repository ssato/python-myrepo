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
import myrepo.tests.common as C

import os.path
import shlex
import unittest


class Test_00_functions(unittest.TestCase):

    def test_10_mk_repos(self):
        """TODO: Implement test cases for mk_repos"""
        pass

    def test_20__assert_no_arg(self):
        TT._assert_no_arg([], None)  # Exp not raised.
        self.assertRaises(AssertionError, TT._assert_no_arg,
                          ["extra_arg_0"], "cmd")

    def test_30__assert_arg(self):
        TT._assert_arg(["arg1"], None)
        self.assertRaises(AssertionError, TT._assert_arg, [], "cmd")

    def test_40__to_cmd(self):
        self.assertEquals(TT._to_cmd(['i']), "init")
        self.assertEquals(TT._to_cmd(["genc"]), "genconf")
        self.assertEquals(TT._to_cmd(['b', "dummy.src.rpm"]), "build")
        self.assertEquals(TT._to_cmd(['d', "dummy.src.rpm"]), "deploy")
        self.assertEquals(TT._to_cmd(['abc']), None)


_CONF_0 = """[DEFAULT]
hostname: localhost
email: jdoe@example.com
name: fedora-com-example-jdoe
workdir: %(workdir)s
baseurl: file://%(workdir)s
dists: fedora-19-x86_64,fedora-19-i386,rhel-6-x86_64
"""


class Test_10_modmain(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_10_init__w_no_genconf(self):
        """FIXME: Implement test codes for myrepo.cli.modmain"""
        return

        conf = os.path.join(self.workdir, "00_localhost.conf")
        open(conf, 'w').write(_CONF_0 % {"workdir": self.workdir})

        c = "myrepo init --config %s --no-genconf" % conf
        cs = shlex.split(c)

        self.assertEquals(TT.modmain(cs), 0)


# vim:sw=4:ts=4:et:
