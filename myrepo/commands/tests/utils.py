#
# Copyright (C) 2013 Red Hat, Inc.
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
import myrepo.commands.utils as TT
import myrepo.repo as MR
import myrepo.srpm as MS
import myrepo.tests.common as C

import logging
import os.path
import unittest


_REMOTE_REPO_0 = MR.Repo("fedora", 19, ["x86_64", "i386"],
                         MR.Server("yumrepos-1.local", "jdoe"))


class Test_00_pure_functions(unittest.TestCase):

    def test_00_assert_repo__ok(self):
        TT.assert_repo(_REMOTE_REPO_0)

    def test_02_assert_repo__ng(self):
        with self.assertRaises(AssertionError) as cm:
            TT.assert_repo(None)

    def test_10_assert_srpm__ok(self):
        srpm = MS.Srpm("/a/b/c/dummy/path/to/srpm.rpm")
        TT.assert_srpm(srpm)

    def test_12_assert_srpm__ng(self):
        with self.assertRaises(AssertionError) as cm:
            TT.assert_srpm(None)

    def test_30_init_workdir__dir_exists(self):
        self.assertEquals(TT.init_workdir("/tmp"), "/tmp")


class Test_10_effecful_functions(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_20_setup_workdir(self):
        prefix = "tt-"
        wdir = TT.setup_workdir(prefix=prefix, topdir=self.workdir)

        self.assertTrue(os.path.basename(wdir).startswith(prefix))
        self.assertTrue(os.path.exists(wdir))

    def test_30_init_workdir__dir_not_exists(self):
        wdir = os.path.join(self.workdir, "wdir")

        wdir_result = TT.init_workdir(wdir)
        self.assertEquals(wdir_result, wdir)
        self.assertTrue(os.path.exists(wdir_result))

# vim:sw=4:ts=4:et:
