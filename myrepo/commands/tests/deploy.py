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
import myrepo.commands.deploy as TT
import myrepo.commands.build as MCB
import myrepo.repo as MR
import myrepo.srpm as MS
import myrepo.utils as MU
import myrepo.tests.common as C

import os.path
import unittest


def _join(*cs):
    return " && ".join(cs)


class Test_00_pure_functions(unittest.TestCase):

    def test_00_prepare_0__localhost_noarch_multi_archs_repo(self):
        server = MR.Server("localhost", topdir="/tmp/yum",
                           baseurl="file:///tmp")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server)

        srpm = MS.Srpm("/a/b/c/dummy.src.rpm")
        srpm.name = "foo"
        srpm.version = "1.0"
        srpm.noarch = True

        dcmd = repo.server.deploy_cmd

        c0 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.src.rpm",
                  "/tmp/yum/fedora/19/sources")
        c1 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.noarch.rpm",
                  "/tmp/yum/fedora/19/x86_64")

        ctx = dict(other_archs_s="i386", primary_arch="x86_64",
                   noarch_rpms="foo-1.0-*.noarch.rpm")
        c2 = "cd /tmp/yum/fedora/19 && " + TT._MK_SYMLINKS_TO_NOARCH_RPM % ctx

        cs_expected = [c0, "%s && %s" % (c1, c2)]
        self.assertListEqual(TT.prepare_0(repo, srpm), cs_expected)

    def test_01_prepare_0__localhost_noarch_multi_archs_repo_w_build(self):
        server = MR.Server("localhost", topdir="/tmp/yum",
                           baseurl="file:///tmp")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server)

        srpm = MS.Srpm("/a/b/c/dummy.src.rpm")
        srpm.name = "foo"
        srpm.version = "1.0"
        srpm.noarch = True

        bcmds = MCB.prepare_0(repo, srpm)

        dcmd = repo.server.deploy_cmd
        c0 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.src.rpm",
                  "/tmp/yum/fedora/19/sources")
        c1 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.noarch.rpm",
                  "/tmp/yum/fedora/19/x86_64")

        ctx = dict(other_archs_s="i386", primary_arch="x86_64",
                   noarch_rpms="foo-1.0-*.noarch.rpm")
        c2 = "cd /tmp/yum/fedora/19 && " + TT._MK_SYMLINKS_TO_NOARCH_RPM % ctx

        cs_expected = [_join(bcmds[0], c0, c1, c2)]
        self.assertListEqual(TT.prepare_0(repo, srpm, True), cs_expected)

    def test_02_prepare_0__localhost_noarch_single_arch_repo(self):
        server = MR.Server("localhost", topdir="/tmp/yum",
                           baseurl="file:///tmp")
        repo = MR.Repo("fedora", 19, ["x86_64"], server)

        srpm = MS.Srpm("/a/b/c/dummy.src.rpm")
        srpm.name = "foo"
        srpm.version = "1.0"
        srpm.noarch = True

        dcmd = repo.server.deploy_cmd
        c0 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.src.rpm",
                  "/tmp/yum/fedora/19/sources")
        c1 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.noarch.rpm",
                  "/tmp/yum/fedora/19/x86_64")

        cs_expected = [c0, c1]
        self.assertListEqual(TT.prepare_0(repo, srpm), cs_expected)

    def test_03_prepare_0__localhost_noarch_single_arch_repo_w_build(self):
        server = MR.Server("localhost", topdir="/tmp/yum",
                           baseurl="file:///tmp")
        repo = MR.Repo("fedora", 19, ["x86_64"], server)

        srpm = MS.Srpm("/a/b/c/dummy.src.rpm")
        srpm.name = "foo"
        srpm.version = "1.0"
        srpm.noarch = True

        bcmds = MCB.prepare_0(repo, srpm)

        dcmd = repo.server.deploy_cmd
        c0 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.src.rpm",
                  "/tmp/yum/fedora/19/sources")
        c1 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.noarch.rpm",
                  "/tmp/yum/fedora/19/x86_64")

        cs_expected = [_join(bcmds[0], c0, c1)]
        self.assertListEqual(TT.prepare_0(repo, srpm, True), cs_expected)

    def test_04_prepare_0__localhost(self):
        server = MR.Server("localhost", topdir="/tmp/yum",
                           baseurl="file:///tmp")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server)

        srpm = MS.Srpm("/a/b/c/dummy.src.rpm")
        srpm.name = "foo"
        srpm.version = "1.0"
        srpm.noarch = False

        dcmd = repo.server.deploy_cmd
        c0 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.src.rpm",
                  "/tmp/yum/fedora/19/sources")
        c1 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.x86_64.rpm",
                  "/tmp/yum/fedora/19/x86_64")
        c2 = dcmd("/var/lib/mock/fedora-19-i386/result/foo-1.0-*.i386.rpm",
                  "/tmp/yum/fedora/19/i386")

        cs_expected = [c0, c1, c2]
        self.assertListEqual(TT.prepare_0(repo, srpm), cs_expected)

    def test_05_prepare_0__localhost_w_build(self):
        server = MR.Server("localhost", topdir="/tmp/yum",
                           baseurl="file:///tmp")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server)

        srpm = MS.Srpm("/a/b/c/dummy.src.rpm")
        srpm.name = "foo"
        srpm.version = "1.0"
        srpm.noarch = False

        bcs = MCB.prepare_0(repo, srpm)

        dcmd = repo.server.deploy_cmd
        c0 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.src.rpm",
                  "/tmp/yum/fedora/19/sources")
        c1 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.x86_64.rpm",
                  "/tmp/yum/fedora/19/x86_64")
        c2 = dcmd("/var/lib/mock/fedora-19-i386/result/foo-1.0-*.i386.rpm",
                  "/tmp/yum/fedora/19/i386")

        cs_expected = [_join(bcs[0], c1, c0), _join(bcs[1], c2)]
        self.assertListEqual(TT.prepare_0(repo, srpm, True), cs_expected)

    def test_10_prepare__localhost_noarch(self):
        server = MR.Server("localhost", topdir="/tmp/yum",
                           baseurl="file:///tmp")
        repos = [MR.Repo("fedora", 18, ["x86_64", "i386"], server),
                 MR.Repo("fedora", 19, ["x86_64", "i386"], server),
                 MR.Repo("rhel", 6, ["x86_64", ], server)]

        srpm = MS.Srpm("/a/b/c/dummy.src.rpm")
        srpm.name = "foo"
        srpm.version = "1.0"
        srpm.noarch = True

        cs_expected = []

        dcmd = repos[0].server.deploy_cmd
        c0 = dcmd("/var/lib/mock/fedora-18-x86_64/result/foo-1.0-*.src.rpm",
                  "/tmp/yum/fedora/18/sources")
        c1 = dcmd("/var/lib/mock/fedora-18-x86_64/result/foo-1.0-*.noarch.rpm",
                  "/tmp/yum/fedora/18/x86_64")
        ctx = dict(other_archs_s="i386", primary_arch="x86_64",
                   noarch_rpms="foo-1.0-*.noarch.rpm")
        c2 = "cd /tmp/yum/fedora/18 && " + TT._MK_SYMLINKS_TO_NOARCH_RPM % ctx
        cs_expected.append(c0)
        cs_expected.append("%s && %s" % (c1, c2))

        dcmd = repos[1].server.deploy_cmd
        c0 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.src.rpm",
                  "/tmp/yum/fedora/19/sources")
        c1 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.noarch.rpm",
                  "/tmp/yum/fedora/19/x86_64")
        ctx = dict(other_archs_s="i386", primary_arch="x86_64",
                   noarch_rpms="foo-1.0-*.noarch.rpm")
        c2 = "cd /tmp/yum/fedora/19 && " + TT._MK_SYMLINKS_TO_NOARCH_RPM % ctx
        cs_expected.append(c0)
        cs_expected.append("%s && %s" % (c1, c2))

        dcmd = repos[2].server.deploy_cmd
        c0 = dcmd("/var/lib/mock/rhel-6-x86_64/result/foo-1.0-*.src.rpm",
                  "/tmp/yum/rhel/6/sources")
        c1 = dcmd("/var/lib/mock/rhel-6-x86_64/result/foo-1.0-*.noarch.rpm",
                  "/tmp/yum/rhel/6/x86_64")
        cs_expected.append(c0)
        cs_expected.append(c1)

        self.assertListEqual(TT.prepare(repos, srpm), cs_expected)

    def test_12_prepare__localhost_noarch_w_build(self):
        server = MR.Server("localhost", topdir="/tmp/yum",
                           baseurl="file:///tmp")
        repos = [MR.Repo("fedora", 18, ["x86_64", "i386"], server),
                 MR.Repo("fedora", 19, ["x86_64", "i386"], server),
                 MR.Repo("rhel", 6, ["x86_64", ], server)]

        srpm = MS.Srpm("/a/b/c/dummy.src.rpm")
        srpm.name = "foo"
        srpm.version = "1.0"
        srpm.noarch = True

        cs_expected = []

        bcs = MCB.prepare_0(repos[0], srpm)  # ['mock -r fedora-18-x86_64 ...']
        dcmd = repos[0].server.deploy_cmd
        c0 = dcmd("/var/lib/mock/fedora-18-x86_64/result/foo-1.0-*.src.rpm",
                  "/tmp/yum/fedora/18/sources")
        c1 = dcmd("/var/lib/mock/fedora-18-x86_64/result/foo-1.0-*.noarch.rpm",
                  "/tmp/yum/fedora/18/x86_64")
        ctx = dict(other_archs_s="i386", primary_arch="x86_64",
                   noarch_rpms="foo-1.0-*.noarch.rpm")
        c2 = "cd /tmp/yum/fedora/18 && " + TT._MK_SYMLINKS_TO_NOARCH_RPM % ctx
        cs_expected.append(_join(bcs[0], c0, c1, c2))

        bcs = MCB.prepare_0(repos[1], srpm)  # ['mock -r fedora-19-x86_64 ...']
        dcmd = repos[1].server.deploy_cmd
        c0 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.src.rpm",
                  "/tmp/yum/fedora/19/sources")
        c1 = dcmd("/var/lib/mock/fedora-19-x86_64/result/foo-1.0-*.noarch.rpm",
                  "/tmp/yum/fedora/19/x86_64")
        ctx = dict(other_archs_s="i386", primary_arch="x86_64",
                   noarch_rpms="foo-1.0-*.noarch.rpm")
        c2 = "cd /tmp/yum/fedora/19 && " + TT._MK_SYMLINKS_TO_NOARCH_RPM % ctx
        cs_expected.append(_join(bcs[0], c0, c1, c2))

        bcs = MCB.prepare_0(repos[2], srpm)  # ['mock -r rhel-6-x86_64 ...']
        dcmd = repos[2].server.deploy_cmd
        c0 = dcmd("/var/lib/mock/rhel-6-x86_64/result/foo-1.0-*.src.rpm",
                  "/tmp/yum/rhel/6/sources")
        c1 = dcmd("/var/lib/mock/rhel-6-x86_64/result/foo-1.0-*.noarch.rpm",
                  "/tmp/yum/rhel/6/x86_64")
        cs_expected.append(_join(bcs[0], c0, c1))

        self.assertListEqual(TT.prepare(repos, srpm, True), cs_expected)


class Test_10_effecful_functions(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_20_run__localhost(self):
        """FIXME: Add test cases for myrepo.commands.deploy.run.
        """
        return

        topdir = os.path.join(self.workdir, "yum")
        server = MR.Server("localhost", topdir=topdir, baseurl="file:///tmp")
        repos = [MR.Repo("fedora", 18, ["x86_64", "i386"], server),
                 MR.Repo("fedora", 19, ["x86_64", "i386"], server),
                 MR.Repo("rhel", 6, ["x86_64", ], server)]
        ctx = dict(repos=repos)

        repos_destdirs = MU.uconcat([os.path.join(repo.destdir, a) for a in
                                    repo.archs] for repo in repos)

        for d in repos_destdirs:
            os.makedirs(d)  # Create repo dirs instead of initialization.

        self.assertTrue(TT.run(ctx))

        for d in repos_destdirs:
            self.assertTrue(os.path.exists(os.path.join(d, "repodata")),
                            "Failed to create %s/repodata !" % d)


# vim:sw=4:ts=4:et:
