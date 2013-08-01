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
import myrepo.commands as TT
import myrepo.repo as R
import myrepo.tests.common as C
import rpmkit.environ as E

import datetime
import os.path
import time
import unittest


# see result.repo.0 also.
_SERVER_0 = R.RepoServer("yumrepos.local", "jdoe", "yumrepos.example.com")
_SERVER_1 = R.RepoServer("localhost", E.get_username())

_REPO_0 = R.Repo("fedora-custom", 19, ["x86_64", "i386"], "fedora",
                 _SERVER_0)

_REPO_1 = R.Repo("fedora-custom", 19, ["x86_64", "i386"], "fedora",
                 _SERVER_1)


class Test_00(unittest.TestCase):

    def test_00__datestamp_w_arg(self):
        d = datetime.datetime(2013, 7, 31)
        self.assertEquals(TT._datestamp(d), 'Wed Jul 31')

    def test_10_gen_repo_file_content(self):
        server = _SERVER_0
        repo = _REPO_0

        ref = C.readfile("result.repo.0")
        s = TT.gen_repo_file_content(repo, C.template_paths())

        self.assertEquals(s, ref, C.diff(s, ref))

    def test_20_gen_mock_cfg_content(self):
        server = _SERVER_0
        repo = _REPO_0

        c = C.readfile("result.repo.0")
        ref = C.readfile("result.mock.cfg.0").replace("REPO_FILE_CONTENT", c)

        s = TT.gen_mock_cfg_content(repo, repo.dists[0], C.template_paths())

        self.assertEquals(s, ref, C.diff(s, ref))

    def test_30_gen_rpmspec_content(self):
        dstamp = TT._datestamp()
        ctx = dict(repo=_REPO_0, version="0.0.1", datestamp=dstamp,
                   fullname="John Doe", email="jdoe@example.com")

        ref = C.readfile("result.yum-repodata.spec.0").replace("DATESTAMP",
                                                               dstamp)
        s = TT.gen_rpmspec_content(ctx, C.template_paths())

        self.assertEquals(s, ref, C.diff(s, ref))

    def test_40_sign_rpms_cmd(self):
        ref = C.readfile("result.sign_rpms.0")
        s = TT.sign_rpms_cmd("XYZ01234", ["aaa-0.1-1.noarch.rpm",
                                          "aaa-bbb-0.1-1.noarch.rpm",
                                          "aaa-ccc-0.1-1.noarch.rpm"])

        self.assertEquals(s.strip(), ref.strip(), C.diff(s, ref))


class Test_10(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()
        self.repo = _REPO_1

    def tearDown(self):
        #C.cleanup_workdir(self.workdir)
        pass

    def test_00_init__no_genconf(self):
        ctx = dict(repo=self.repo)
        ctx["genconf"] = False

        self.assertTrue(TT.init(ctx))

        for d in self.repo.rpmdirs:
            if '~' in d:
                d = os.path.expanduser(d)

            self.assertTrue(os.path.exists(d), d)

    def test_30_init_and_update(self):
        return

        ctx = dict(repo=self.repo)
        ctx["genconf"] = False

        self.assertTrue(TT.init(ctx))
        self.assertTrue(TT.update(ctx))

# vim:sw=4:ts=4:et:
