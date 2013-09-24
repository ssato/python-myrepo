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
import myrepo.commands.init as TT
import myrepo.repo as MR
import myrepo.tests.common as C

import os.path
import unittest


def mk_local_repos(topdir="/tmp"):
    server = MR.Server("localhost", user="jdoe",
                       topdir=os.path.join(topdir, "yum"))
    assert isinstance(server, MR.Server)

    return [MR.Repo("fedora", 18, ["x86_64", "i386"], server),
            MR.Repo("fedora", 19, ["x86_64", "i386"], server),
            MR.Repo("rhel", 6, ["x86_64", ], server)]


def mk_remote_repos():
    server = MR.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
    assert isinstance(server, MR.Server)

    reponame = "%(name)s-%(server_shortaltname)s"
    return [MR.Repo("fedora", 18, ["x86_64", "i386"], server, reponame),
            MR.Repo("fedora", 19, ["x86_64", "i386"], server, reponame),
            MR.Repo("rhel", 6, ["x86_64", ], server, reponame)]


class Test_00_pure_functions(unittest.TestCase):

    def test_00_prepare_0__localhost(self):
        repo = mk_local_repos()[0]

        # TODO: Which is better ?
        #cs_expected = ["mkdir -p %s" %
        #               TT._join_dirs(repo.destdir, repo.archs + ["sources"])]
        cs_expected = ["mkdir -p /tmp/yum/fedora/18/{x86_64,i386,sources}", ]

        self.assertListEqual(TT.prepare_0(repo), cs_expected)

    def test_02_prepare_0__remotehost(self):
        repo = mk_remote_repos()[0]

        # TODO: Generate 'ssh ...' preamble.
        cs_expected = ["ssh -o ConnectTimeout=10 jdoe@yumrepos-1.local " +
                       "'mkdir -p " +
                       os.path.join("~jdoe/public_html/",
                                    "yum/fedora/18/{x86_64,i386,sources}'")]

        self.assertListEqual(TT.prepare_0(repo), cs_expected)

    def test_10_prepare__localhost(self):
        repos = mk_local_repos()

        # TODO: Likewise
        cs_expected = ["mkdir -p /tmp/yum/fedora/18/{x86_64,i386,sources}",
                       "mkdir -p /tmp/yum/fedora/19/{x86_64,i386,sources}",
                       "mkdir -p /tmp/yum/rhel/6/{x86_64,sources}"]

        self.assertListEqual(TT.prepare(repos), cs_expected)

    def test_12_prepare__remotehost(self):
        repos = mk_remote_repos()

        # TODO: Likewise
        cs_expected = [
            "ssh -o ConnectTimeout=10 jdoe@yumrepos-1.local 'mkdir -p " +
            "~jdoe/public_html/yum/fedora/18/{x86_64,i386,sources}'",
            "ssh -o ConnectTimeout=10 jdoe@yumrepos-1.local 'mkdir -p " +
            "~jdoe/public_html/yum/fedora/19/{x86_64,i386,sources}'",
            "ssh -o ConnectTimeout=10 jdoe@yumrepos-1.local 'mkdir -p " +
            "~jdoe/public_html/yum/rhel/6/{x86_64,sources}'"
        ]

        self.assertListEqual(TT.prepare(repos), cs_expected)


class Test_10_effecful_functions(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_20_run__localhost(self):
        ctx = dict(repos=mk_local_repos(self.workdir), )
        self.assertTrue(TT.run(ctx))

        for dn in ("fedora/18", "fedora/19", "rhel/6"):
            for d in ("x86_64", "i386", "sources"):
                self.assertTrue(os.path.join(self.workdir, "yum", dn, d))

    def test_30_run__localhost_w_genconf(self):
        return  # Wait for test cases fixes of myrepo.commands.genconf.*.

        builddir = os.path.join(self.workdir, "build")
        repos = mk_local_repos(self.workdir)

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
