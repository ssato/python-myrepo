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


# vim:sw=4:ts=4:et:
