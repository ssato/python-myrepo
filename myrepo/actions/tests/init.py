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
import myrepo.actions.init as TT
import myrepo.repo as MR
import myrepo.utils as MU
import myrepo.tests.common as C

import itertools
import os.path
import unittest


class Test_00_pure_functions(unittest.TestCase):

    def test_00_prepare_0__localhost(self):
        server = MR.Server("localhost", topdir="/tmp/yum")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server)

        cs_expected = ["mkdir -p %s" %
                       TT._join_dirs(repo.destdir, repo.archs + ["sources"])]
        cs = TT.prepare_0(repo)

        for c, exp in itertools.izip(cs, cs_expected):
            self.assertEquals(c, exp)

    def test_10_prepare__localhost(self):
        server = MR.Server("localhost", topdir="/tmp/yum")
        repos = [MR.Repo("fedora", 18, ["x86_64", "i386"], server),
                 MR.Repo("fedora", 19, ["x86_64", "i386"], server),
                 MR.Repo("rhel", 6, ["x86_64", ], server)]

        def cs_expected_gen(repo):
            return ["mkdir -p %s" %
                    TT._join_dirs(repo.destdir, repo.archs + ["sources"])]

        cs_expected = MU.concat(cs_expected_gen(repo) for repo in repos)
        cs = TT.prepare(repos)

        for c, exp in itertools.izip(cs, cs_expected):
            self.assertEquals(c, exp)


class Test_10_effecful_functions(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        #C.cleanup_workdir(self.workdir)
        pass

    def test_20_run__localhost(self):
        return
        topdir = os.path.join(self.workdir, "yum")
        server = MR.Server("localhost", topdir=topdir)
        repos = [MR.Repo("fedora", 18, ["x86_64", "i386"], server),
                 MR.Repo("fedora", 19, ["x86_64", "i386"], server),
                 MR.Repo("rhel", 6, ["x86_64", ], server)]
        ctx = dict(repos=repos)

        def expected_dirs(repo):
            return [os.path.join(repo.destdir, a) for a
                    in repo.archs + ["sources"]]

        self.assertTrue(TT.run(ctx))

        for repo in repos:
            for d in expected_dirs(repo):
                self.assertTrue(os.path.exists(d), "Failed to create " + d)

    def test_30_run__localhost_w_genconf(self):
        topdir = os.path.join(self.workdir, "yum")
        builddir = os.path.join(self.workdir, "build")

        server = MR.Server("localhost", user="jdoe", topdir=topdir)
        repos = [MR.Repo("fedora", 18, ["x86_64", "i386"], server),
                 MR.Repo("fedora", 19, ["x86_64", "i386"], server),
                 MR.Repo("rhel", 6, ["x86_64", ], server)]

        ctx = dict(repos=repos, fullname="John Doe", email="jdoe@example.com",
                   workdir=builddir, tpaths=C.template_paths(),
                   genconf=True)

        def expected_dirs(repo):
            return [os.path.join(repo.destdir, a) for a
                    in repo.archs + ["sources"]]

        self.assertTrue(TT.run(ctx))

        for repo in repos:
            for d in expected_dirs(repo):
                self.assertTrue(os.path.exists(d), "Failed to create " + d)

# vim:sw=4:ts=4:et:
