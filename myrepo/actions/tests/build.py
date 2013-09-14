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
import myrepo.actions.build as TT
import myrepo.repo as MR
import myrepo.srpm as MS
import myrepo.utils as MU
import myrepo.tests.common as C

import itertools
import logging
import os.path
import unittest


class Test_00_pure_functions(unittest.TestCase):

    def test_00_prepare_0(self):
        server = MR.Server("localhost")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server)
        srpm = MS.Srpm("/path/to/dummy-0.1.src.rpm")
        srpm.noarch = False

        cs_expected = ["mock -r fedora-19-x86_64 %s" % srpm.path,
                       "mock -r fedora-19-i386 %s" % srpm.path]
        cs = TT.prepare_0(repo, srpm, logging.INFO)

        for c, exp in itertools.izip(cs, cs_expected):
            self.assertEquals(c, exp)

    def test_02_prepare_0_noarch(self):
        server = MR.Server("localhost")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server)
        srpm = MS.Srpm("/path/to/dummy-0.1.src.rpm")
        srpm.noarch = True

        cs_expected = ["mock -r fedora-19-x86_64 %s" % srpm.path]
        cs = TT.prepare_0(repo, srpm, logging.INFO)

        for c, exp in itertools.izip(cs, cs_expected):
            self.assertEquals(c, exp)

    def test_04_prepare_0_noarch__reponame(self):
        server = MR.Server("localhost")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server,
                       reponame="fedora-custom", build_for_self=True)
        srpm = MS.Srpm("/path/to/dummy-0.1.src.rpm")
        srpm.noarch = True

        cs_expected = ["mock -r fedora-custom-19-x86_64 %s" % srpm.path]
        cs = TT.prepare_0(repo, srpm, logging.INFO)

        for c, exp in itertools.izip(cs, cs_expected):
            self.assertEquals(c, exp)

    def test_10_prepare__noarch(self):
        server = MR.Server("localhost")
        repos = [MR.Repo("fedora", 18, ["x86_64", "i386"], server),
                 MR.Repo("fedora", 19, ["x86_64", "i386"], server),
                 MR.Repo("rhel", 6, ["x86_64", ], server)]
        srpm = MS.Srpm("/path/to/dummy-0.1.src.rpm")
        srpm.noarch = True

        cs_expected = ["mock -r fedora-18-x86_64 %s" % srpm.path,
                       "mock -r fedora-19-x86_64 %s" % srpm.path,
                       "mock -r rhel-6-x86_64 %s" % srpm.path]
        cs = TT.prepare(repos, srpm, logging.INFO)

        for c, exp in itertools.izip(cs, cs_expected):
            self.assertEquals(c, exp)


class Test_10_effecful_functions(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_20_run__localhost(self):
        """FIXME: Add test cases for myrepo.actions.build.run."""
        return


# vim:sw=4:ts=4:et:
