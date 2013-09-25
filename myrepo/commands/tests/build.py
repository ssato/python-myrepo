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
import myrepo.commands.build as TT
import myrepo.repo as MR
import myrepo.srpm as MS
import myrepo.utils as MU
import myrepo.tests.common as C

import glob
import itertools
import logging
import os.path
import subprocess
import unittest


CURDIR = os.path.dirname(__file__)


def mk_local_repos(**kwargs):
    server = MR.Server("localhost")
    return [MR.Repo("fedora", 18, ["x86_64", "i386"], server, **kwargs),
            MR.Repo("fedora", 19, ["x86_64", "i386"], server, **kwargs),
            MR.Repo("rhel", 6, ["x86_64", ], server, **kwargs)]


def build_sample_rpm_if_not_exist():
    rpms = glob.glob(os.path.join(CURDIR, "rpm-sample-*.src.rpm"))

    if rpms:
        return rpms[0]

    subprocess.check_call(os.path.join(CURDIR, "rpm-sample-build.sh"),
                          shell=True)
    return glob.glob(os.path.join(CURDIR, "rpm-sample-*.src.rpm"))[0]


class Test_00_pure_functions(unittest.TestCase):

    def setUp(self):
        self.repos = mk_local_repos()
        self.repo = self.repos[1]  # fedora-19-*
        self.srpm = MS.Srpm(build_sample_rpm_if_not_exist())
        self.srpm.resolve()

    def test_00_prepare_0(self):
        (repo, srpm) = (self.repo, self.srpm)
        srpm.noarch = False  # Override it.

        cs_expected = ["mock -r fedora-19-x86_64 %s" % srpm.path,
                       "mock -r fedora-19-i386 %s" % srpm.path]
        cs = TT.prepare_0(repo, srpm, logging.INFO)

        self.assertListEqual(cs, cs_expected)

    def test_02_prepare_0_noarch(self):
        (repo, srpm) = (self.repo, self.srpm)

        cs_expected = ["mock -r fedora-19-x86_64 %s" % srpm.path]
        cs = TT.prepare_0(repo, srpm, logging.INFO)

        self.assertListEqual(cs, cs_expected)

    def test_04_prepare_0_noarch__reponame(self):
        repo = mk_local_repos(reponame="fedora-custom", selfref=True)[1]
        srpm = self.srpm

        cs_expected = ["mock -r fedora-custom-19-x86_64 %s" % srpm.path]
        cs = TT.prepare_0(repo, srpm, logging.INFO)

        self.assertListEqual(cs, cs_expected)

    def test_10_prepare__noarch(self):
        (repos, srpm) = (self.repos, self.srpm)

        cs_expected = ["mock -r fedora-18-x86_64 %s" % srpm.path,
                       "mock -r fedora-19-x86_64 %s" % srpm.path,
                       "mock -r rhel-6-x86_64 %s" % srpm.path]
        cs = TT.prepare(repos, srpm, logging.INFO)

        self.assertListEqual(cs, cs_expected)


class Test_10_effecful_functions(unittest.TestCase):

    def setUp(self):
        self.repos = mk_local_repos()
        self.repo = self.repos[1]  # fedora-19-*
        self.srpm = MS.Srpm(build_sample_rpm_if_not_exist())
        self.srpm.resolve()

        self.workdir = C.setup_workdir()

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_20_run__localhost_noarch(self):
        (repo, srpm) = (self.repo, self.srpm)
        ctx = dict(repos=[repo], srpm=srpm)

        ctx2 = ctx.copy()
        ctx2["dryrun"] = True

        self.assertTrue(TT.run(ctx2))
        self.assertTrue(TT.run(ctx))


# vim:sw=4:ts=4:et:
