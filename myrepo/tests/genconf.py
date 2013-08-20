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
import myrepo.genconf as TT
import myrepo.repo as MR
import myrepo.tests.common as C

import datetime
import logging
import os.path
import unittest


class Test_00_functions(unittest.TestCase):

    def test_00__datestamp_w_arg(self):
        d = datetime.datetime(2013, 7, 31)
        self.assertEquals(TT._datestamp(d), 'Wed Jul 31 2013')

    def test_10_gen_repo_file_content(self):
        server = MR.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server,
                       "%(name)s-%(server_shortaltname)s")

        ref = C.readfile("result.repo.0")
        ctx = repo.as_dict()

        s = TT.gen_repo_file_content(ctx, C.template_paths())

        self.assertEquals(s, ref, C.diff(s, ref))

    def test_20_gen_mock_cfg_content(self):
        ref = C.readfile("result.mock.cfg.0")
        ctx = dict(base_mockcfg="fedora-19-x86_64.cfg",
                   mock_root="fedora-custom-19-x86_64",
                   repo_file_content="REPO_FILE_CONTENT")

        s = TT.gen_mock_cfg_content(ctx, C.template_paths())
        self.assertEquals(s, ref, C.diff(s, ref))

    def test_30_gen_rpmspec_content(self):
        server = MR.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server,
                       "%(name)s-%(server_shortaltname)s")
        ctx = dict(repo=repo, fullname="John Doe", email="jdoe@example.com")

        ref = C.readfile("result.yum-repodata.spec.0").strip()
        ref = ref.replace("DATESTAMP", TT._datestamp())

        s = TT.gen_rpmspec_content(ctx, C.template_paths()).strip()
        self.assertEquals(s, ref, C.diff(s, ref))


class Test_10_effectful_functions(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_10_gen_repo_files(self):
        server = MR.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server,
                       "%(name)s-%(server_shortaltname)s")

        fs = TT.gen_repo_files(repo, self.workdir, C.template_paths())

        refs = [C.readfile("result.repo.files.0"),
                C.readfile("result.mock.cfg.files.x86_64"),
                C.readfile("result.mock.cfg.files.i386")]

        for f in fs:
            if f.endswith(".repo"):
                ref = C.readfile("result.repo.files.0")
            else:
                if f.endswith("x86_64.cfg"):
                    ref = C.readfile("result.mock.cfg.files.x86_64")
                else:
                    ref = C.readfile("result.mock.cfg.files.i386")

            self.assertTrue(os.path.isfile(f))

            # normalize whitespaces and empty lines:
            s = open(f).read().strip()
            ref = ref.strip()

            self.assertEquals(s, ref, "f=%s\n" % f + C.diff(s, ref))

    def test_30_gen_rpmspec(self):
        server = MR.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server,
                       "%(name)s-%(server_shortaltname)s")
        ctx = dict(repo=repo, fullname="John Doe", email="jdoe@example.com")

        ref = C.readfile("result.yum-repodata.spec.0").strip()
        ref = ref.replace("DATESTAMP", TT._datestamp())

        f = TT.gen_rpmspec(ctx, self.workdir, C.template_paths())
        s = open(f).read().strip()

        self.assertTrue(os.path.exists(f))
        self.assertEquals(s, ref, "f=%s\n" % f + C.diff(s, ref))

    def test_40_build_repodata_srpm(self):
        server = MR.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server,
                       "%(name)s-%(server_shortaltname)s")
        ctx = dict(repo=repo, fullname="John Doe", email="jdoe@example.com")

        srpm = TT.build_repodata_srpm(ctx, self.workdir, C.template_paths())

        self.assertFalse(srpm is None)
        self.assertTrue(os.path.exists(srpm))


# vim:sw=4:ts=4:et:
