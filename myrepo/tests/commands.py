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
import logging
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

_REPO_2 = R.Repo("fedora-custom", 19, ["x86_64", "i386"], "fedora",
                 _SERVER_1, "%(base_name)s-%(version)s")


def _gen_repo(server, name="fedora-custom", version=19,
              archs=["x86_64", "i386"], base_name="fedora", **kwargs):
    """
    Generate R.Repo object.
    """
    assert isinstance(server, R.RepoServer)
    return R.Repo(name, version, archs, base_name, server, **kwargs)


def _gen_local_fs_repo(workdir):
    s = R.RepoServer("localhost", E.get_username(), topdir=workdir,
                     baseurl="file://" + workdir)
    return R.Repo("fedora-custom", 19, ["x86_64", "i386"], "fedora", s)


class Test_00_functions(unittest.TestCase):

    def test_00__datestamp_w_arg(self):
        d = datetime.datetime(2013, 7, 31)
        self.assertEquals(TT._datestamp(d), 'Wed Jul 31 2013')

    def test_10_gen_repo_file_content(self):
        repo = _REPO_0

        ref = C.readfile("result.repo.0")
        s = TT.gen_repo_file_content(repo, C.template_paths())

        self.assertEquals(s, ref, C.diff(s, ref))

    def test_20_gen_mock_cfg_content(self):
        repo = _REPO_0

        c = C.readfile("result.repo.0")
        ref = C.readfile("result.mock.cfg.0").replace("REPO_FILE_CONTENT", c)

        s = TT.gen_mock_cfg_content(repo, repo.dists[0], C.template_paths())

        self.assertEquals(s, ref, C.diff(s, ref))

    def test_25_gen_mock_cfg_content(self):
        repo = _REPO_2

        c = C.readfile("result.repo.2").replace("USER", E.get_username())
        ref = C.readfile("result.mock.cfg.0").replace("REPO_FILE_CONTENT", c)

        s = TT.gen_mock_cfg_content(repo, repo.dists[0], C.template_paths())

        self.assertEquals(s, ref, C.diff(s, ref))

    def test_30_gen_rpmspec_content(self):
        dstamp = TT._datestamp()
        ctx = dict(repo=_REPO_0, datestamp=dstamp, fullname="John Doe",
                   email="jdoe@example.com")

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

    def test_50__deploy_cmd__remote(self):
        repo = _REPO_0
        s = TT._deploy_cmd(repo, "/a", "/b")

        self.assertEquals(s, "scp -p /a jdoe@yumrepos.local:/b")

    def test_55__deploy_cmd__local(self):
        repo = _REPO_2
        s = TT._deploy_cmd(repo, "/a", "/b")

        self.assertEquals(s, "cp -a /a /b")


class Test_10_effectful_functions(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_10_gen_repo_file(self):
        repo = _REPO_0

        ref = C.readfile("result.repo.0")
        fref = os.path.join(self.workdir, "%s.repo" % repo.dist)

        f = TT.gen_repo_file(repo, self.workdir, C.template_paths())
        s = open(f).read()

        self.assertTrue(os.path.isfile(f))
        self.assertEquals(f, fref)
        self.assertEquals(s, ref, C.diff(s, ref))

    def test_20_gen_rpmspec(self):
        dstamp = TT._datestamp()
        ctx = dict(repo=_REPO_0, datestamp=dstamp,
                   fullname="John Doe", email="jdoe@example.com")

        fref = os.path.join(self.workdir, "yum-repodata.spec")
        ref = C.readfile("result.yum-repodata.spec.0").replace("DATESTAMP",
                                                               dstamp)
        f = TT.gen_rpmspec(ctx, self.workdir, C.template_paths())
        s = open(f).read()

        self.assertTrue(os.path.isfile(f))
        self.assertEquals(f, fref)
        self.assertEquals(s, ref, C.diff(s, ref))


class Test_20_build_functions(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_10_build_repodata_srpm(self):
        dstamp = TT._datestamp()
        ctx = dict(repo=_REPO_0, datestamp=dstamp, fullname="John Doe",
                   email="jdoe@example.com")

        srpm = TT.build_repodata_srpm(ctx, self.workdir,
                                      C.template_paths())

        self.assertFalse(srpm is None)
        self.assertTrue(os.path.isfile(srpm))

    def test_20__dists_by_srpm(self):
        repo = _REPO_0
        dstamp = TT._datestamp()

        ctx = dict(repo=repo, datestamp=dstamp, fullname="John Doe",
                   email="jdoe@example.com")

        srpm = TT.build_repodata_srpm(ctx, self.workdir,
                                      C.template_paths())

        dists = TT._dists_by_srpm(repo, srpm)

        self.assertTrue(dists)
        self.assertEquals(dists[0], repo.dists[0])

    def test_30__build(self):
        repo = _REPO_2
        dstamp = TT._datestamp()

        ctx = dict(repo=repo, datestamp=dstamp, fullname="John Doe",
                   email="jdoe@example.com")

        logging.getLogger().setLevel(logging.WARN)
        srpm = TT.build_repodata_srpm(ctx, self.workdir, C.template_paths())

        logging.getLogger().setLevel(logging.INFO)
        self.assertTrue(os.path.exists(srpm))
        self.assertTrue(TT._build(repo, srpm))

    def test_40__build_srpm(self):
        repo = _REPO_2
        dstamp = TT._datestamp()

        ctx = dict(repo=repo, datestamp=dstamp, fullname="John Doe",
                   email="jdoe@example.com")

        logging.getLogger().setLevel(logging.WARN)
        srpm = TT.build_repodata_srpm(ctx, self.workdir, C.template_paths())

        assert os.path.exists(srpm), "SRPM does not exist: " + str(srpm)
        self.assertTrue(TT._build_srpm(ctx, srpm))

        to_deploy = ctx.get("rpms_to_deploy", False)
        to_sign = ctx.get("rpms_to_sign", False)

        s = "rpms: to_deploy=%s, to_sign=%s" % (str(to_deploy), str(to_sign))

        self.assertTrue(ctx.get("rpms_to_deploy", False), s)
        self.assertTrue(ctx.get("rpms_to_sign", False), s)


class Test_30_commands(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_00_init__no_genconf(self):
        ctx = dict(repo=_gen_local_fs_repo(self.workdir))
        ctx["genconf"] = False

        self.assertTrue(TT.init(ctx))

        for d in ctx["repo"].rpmdirs:
            if '~' in d:
                d = os.path.expanduser(d)

            self.assertTrue(os.path.exists(d), d)

    def test_10_init__w_genconf(self):
        return

        ctx = dict(repo=_gen_local_fs_repo(self.workdir))
        ctx["genconf"] = True
        ctx["tpaths"] = C.template_paths()

        self.assertTrue(TT.init(ctx))

        self.assertTrue(ctx["rpms_to_deploy"])
        self.assertTrue(ctx["rpms_to_sign"])

        for d in ctx["repo"].rpmdirs:
            if '~' in d:
                d = os.path.expanduser(d)

            self.assertTrue(os.path.exists(d), d)

            rpms = glob.glob(os.path.join(d, "*.rpm"))
            self.assertTrue(rpms)

    def test_30_init_and_update(self):
        ctx = dict(repo=_gen_local_fs_repo(self.workdir))
        ctx["genconf"] = False

        self.assertTrue(TT.init(ctx))
        self.assertTrue(TT.update(ctx))

# vim:sw=4:ts=4:et:
