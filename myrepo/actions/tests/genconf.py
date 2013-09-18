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
import myrepo.actions.genconf as TT
import myrepo.repo as MR
import myrepo.tests.common as C

import datetime
import itertools
import logging
import os.path
import unittest


_CURDIR = os.path.dirname(__file__)


class Test_00_pure_functions(unittest.TestCase):

    def test_00__datestamp_w_arg(self):
        d = datetime.datetime(2013, 7, 31)
        self.assertEquals(TT._datestamp(d), 'Wed Jul 31 2013')

    def test_10__check_vars_for_template(self):
        TT._check_vars_for_template({'a', 1}, ['a'])
        with self.assertRaises(AssertionError):
            TT._check_vars_for_template({}, ['a'])

    def test_20_gen_repo_file_content(self):
        server = MR.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server,
                       "%(name)s-%(server_shortaltname)s")

        ref = C.readfile("result.repo.0", _CURDIR)
        s = TT.gen_repo_file_content(repo.as_dict(), C.template_paths())

        self.assertEquals(s, ref, C.diff(s, ref))

    def test_30_gen_mock_cfg_content(self):
        ref = C.readfile("result.mock.cfg.0", _CURDIR)
        ctx = dict(mockcfg="fedora-19-x86_64.cfg",
                   label="fedora-custom-19-x86_64",
                   repo_file_content="REPO_FILE_CONTENT")

        s = TT.gen_mock_cfg_content(ctx, C.template_paths())
        self.assertEquals(s, ref, C.diff(s, ref))

    def test_40_gen_rpmspec_content(self):
        server = MR.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server,
                       "%(name)s-%(server_shortaltname)s")
        ctx = dict(fullname="John Doe", email="jdoe@example.com")

        ref = C.readfile("result.yum-repodata.spec.0", _CURDIR).strip()
        ref = ref.replace("DATESTAMP", TT._datestamp())

        s = TT.gen_rpmspec_content(repo, ctx, C.template_paths()).strip()
        self.assertEquals(s, ref, C.diff(s, ref))

    def test_50_gen_repo_files_g(self):
        server = MR.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server,
                       "%(name)s-%(server_shortaltname)s")
        ctx = dict(fullname="John Doe", email="jdoe@example.com",
                   mockcfg="fedora-19-x86_64.cfg",
                   label="fedora-yumrepos-19-x86_64",
                   repo_file_content="REPO_FILE_CONTENT")
        workdir = "/tmp/myrepo-t-000"

        files = list(TT.gen_repo_files_g(repo, ctx, workdir,
                                         C.template_paths()))

        self.assertTrue(files)
        self.assertEquals(files[0][0],
                          os.path.join(workdir, "fedora-yumrepos.repo"))
        self.assertEquals(files[1][0],
                          os.path.join(workdir,
                                       "fedora-yumrepos-19-x86_64.cfg"))
        self.assertEquals(files[2][0],
                          os.path.join(workdir,
                                       "fedora-yumrepos-19-i386.cfg"))
        self.assertEquals(files[3][0],
                          os.path.join(workdir, "fedora-yumrepos-19.spec"))

    def test_100_prepare(self):
        server = MR.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server,
                       "%(name)s-%(server_shortaltname)s")
        ctx = dict(fullname="John Doe", email="jdoe@example.com",
                   mockcfg="fedora-19-x86_64.cfg",
                   label="fedora-yumrepos-19-x86_64",
                   repo_file_content="REPO_FILE_CONTENT",
                   workdir="/tmp/myrepo-t-000", tpaths=C.template_paths())

        files = list(TT.gen_repo_files_g(repo, ctx, ctx["workdir"],
                                         C.template_paths()))
        counter = itertools.count()
        eof = lambda: "EOF_%d" % counter.next()

        counter2 = itertools.count()
        eof2 = lambda: "EOF_%d" % counter2.next()

        rcs = [TT.mk_write_file_cmd(p, c, eof) for p, c in files] + \
              [TT.mk_build_srpm_cmd(files[-1][0], False)]

        expected = '\n'.join(rcs)
        s = TT.prepare_0(repo, ctx, eof2)[0]

        self.assertEquals(s, expected, C.diff(expected, s))


class Test_10_effectful_functions(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_110_run(self):
        server = MR.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server,
                       "%(name)s-%(server_shortaltname)s")
        ctx = dict(repos=[repo], fullname="John Doe", email="jdoe@example.com",
                   workdir=self.workdir, tpaths=C.template_paths())

        self.assertTrue(TT.run(ctx))

    def test_112_run_multi_repos(self):
        server = MR.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
        reponame = "%(name)s-%(server_shortaltname)s"
        repos = [MR.Repo("fedora", 18, ["x86_64", "i386"], server, reponame),
                 MR.Repo("fedora", 19, ["x86_64", "i386"], server, reponame),
                 MR.Repo("rhel", 19, ["x86_64", "i386"], server, reponame)]
        ctx = dict(repos=repos, fullname="John Doe", email="jdoe@example.com",
                   workdir=self.workdir, tpaths=C.template_paths())

        self.assertTrue(TT.run(ctx))


# vim:sw=4:ts=4:et:
