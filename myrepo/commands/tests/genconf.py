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
from myrepo.srpm import Srpm

import myrepo.commands.genconf as TT
import myrepo.repo as MR
import myrepo.shell as MS
import myrepo.tests.common as C

import datetime
import glob
import itertools
import logging
import os.path
import random
import re
import subprocess
import unittest


_CURDIR = os.path.dirname(__file__)


def mk_remote_repo():
    server = MR.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
    repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server,
                   "%(name)s-%(server_shortaltname)s")
    return repo


def mk_local_repos(topdir="/tmp"):
    server = MR.Server("localhost", topdir=topdir, baseurl="file:///tmp")
    reponame = "%(name)s-%(server_shortaltname)s"

    return [MR.Repo("fedora", 18, ["x86_64", "i386"], server, reponame),
            MR.Repo("fedora", 19, ["x86_64", "i386"], server, reponame),
            MR.Repo("rhel", 6, ["x86_64", ], server, reponame)]


def mk_ctx(repos=[], nrepos=1, remote=True, topdir="/tmp"):
    if not repos:
        if remote:
            repos = [mk_remote_repo()]
        else:
            repos = mk_local_repos(topdir)[:nrepos]

    return dict(repos=repos, fullname="John Doe", email="jdoe@example.com",
                mockcfg="fedora-19-x86_64.cfg", keyid=False,
                label="fedora-yumrepos-19-x86_64",
                repo_file_content="REPO_FILE_CONTENT",
                tpaths=C.template_paths(), workdir="/tmp/myrepo-t-000")


def _find_gpg_keyids():
    output = subprocess.check_output("gpg --list-keys | grep -E '^pub'",
                                     shell=True)
    if output:
        return [l.split()[1].split('/')[1] for l in output.splitlines()]
    else:
        return []


class Test_00_pure_functions(unittest.TestCase):

    def test_000__datestamp_w_arg(self):
        d = datetime.datetime(2013, 7, 31)
        self.assertEquals(TT._datestamp(d), "Wed Jul 31 2013")

    def test_010__check_vars_for_template(self):
        TT._check_vars_for_template({'a', 1}, ['a'])

        with self.assertRaises(AssertionError):
            TT._check_vars_for_template({}, ['a'])

    def test_020_gen_repo_file_content(self):
        ctx = mk_ctx()
        ctx.update(ctx["repos"][0].as_dict())

        ref = C.readfile("result.repo.0", _CURDIR)
        s = TT.gen_repo_file_content(ctx, C.template_paths())

        self.assertEquals(s, ref, C.diff(s, ref))

    def test_022_gen_repo_file_content__w_keyid_and_repo_params(self):
        ctx = mk_ctx()
        ctx.update(ctx["repos"][0].as_dict())

        # Override it:
        ctx["keyid"] = "dummykey001"
        ctx["repo_params"] = ["failovermethod=priority", "metadata_expire=7d"]

        ref = C.readfile("result.repo.1", _CURDIR)
        s = TT.gen_repo_file_content(ctx, C.template_paths())

        self.assertEquals(s, ref, C.diff(s, ref))

    def test_030_gen_mock_cfg_content(self):
        ctx = mk_ctx()
        ref = C.readfile("result.mock.cfg.0", _CURDIR)

        s = TT.gen_mock_cfg_content(ctx, C.template_paths())
        self.assertEquals(s, ref, C.diff(s, ref))

    def test_032_gen_mock_cfg_content(self):
        ctx = mk_ctx()
        ctx["label"] = "fedora-custom-19-x86_64"
        ref = C.readfile("result.mock.cfg.1", _CURDIR)

        s = TT.gen_mock_cfg_content(ctx, C.template_paths())
        self.assertEquals(s, ref, C.diff(s, ref))

    def test_040_gen_rpmspec_content(self):
        repo = mk_remote_repo()
        ctx = mk_ctx([repo])

        ref = C.readfile("result.yum-repodata.spec.0", _CURDIR).strip()
        ref = ref.replace("DATESTAMP", TT._datestamp())

        s = TT.gen_rpmspec_content(repo, ctx, C.template_paths()).strip()
        self.assertEquals(s, ref, C.diff(s, ref))

    def test_050_gen_repo_files_g(self):
        repo = mk_remote_repo()
        ctx = mk_ctx([repo])

        workdir = ctx["workdir"]
        files = list(TT.gen_repo_files_g(repo, ctx, workdir,
                                         C.template_paths()))
        self.assertTrue(files)
        self.assertEquals(files[0][0],
                          os.path.join(workdir, "fedora-yumrepos.repo"))
        self.assertEquals(files[-1][0],
                          os.path.join(workdir, "fedora-yumrepos-19.spec"))

    def test_060_gen_mockcfg_files_cmd_g(self):
        """
        FIXME: test code for myrepo.commands.genconf.gen_mockcfg_files_cmd_g
        """
        repo = mk_remote_repo()
        ctx = mk_ctx([repo])

        eof = lambda: "EOF"
        workdir = ctx["workdir"]
        cmds = list(TT.gen_mockcfg_files_cmd_g(repo, ctx, workdir,
                                               C.template_paths(), eof))
        self.assertTrue(cmds)
        #self.assertEquals(cmds[0], ...)
        #self.assertEquals(cmds[1], ...)

    def test_100_prepare(self):
        repo = mk_remote_repo()
        ctx = mk_ctx([repo])

        files = list(TT.gen_repo_files_g(repo, ctx, ctx["workdir"],
                                         C.template_paths()))
        gmcs = TT.gen_mockcfg_files_cmd_g(repo, ctx, ctx["workdir"],
                                          C.template_paths())

        rcs = ["mkdir -p " + ctx["workdir"]] + \
              [TT.mk_write_file_cmd(p, c) for p, c in files] + \
              list(gmcs) + \
              [TT.mk_build_srpm_cmd(files[-1][0], False)]

        expected = " && ".join(rcs)
        s = TT.prepare_0(repo, ctx)[0]

        # Normalize 'EOF_....' lines:
        expected = re.sub(r"EOF_\S+", "EOF", expected)
        s = re.sub(r"EOF_\S+", "EOF", s)

        self.assertEquals(s, expected, C.diff(expected, s))


class Test_10_effectful_functions(unittest.TestCase):

    def test_42_gen_rpmspec_content__w_keyid(self):
        repo = mk_remote_repo()
        ctx = mk_ctx([repo])

        keyids = _find_gpg_keyids()
        if keyids:
            ctx["keyid"] = keyid = random.choice(keyids)
        else:
            sys.stderr.write("No GPG keyid was found. Skip this test...\n")
            return

        ref = C.readfile("result.yum-repodata.spec.1", _CURDIR).strip()
        ref = ref.replace("DATESTAMP", TT._datestamp())

        s = TT.gen_rpmspec_content(repo, ctx, C.template_paths()).strip()
        self.assertEquals(s, ref, C.diff(s, ref))


class Test_20_effectful_functions(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        #C.cleanup_workdir(self.workdir)
        pass

    def test_070_gen_gpgkey(self):
        return
        server = MR.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
        repo = MR.Repo("fedora", 19, ["x86_64", "i386"], server,
                       "%(name)s-%(server_shortaltname)s")
        ctx = dict(repos=[repo, ],
                   fullname="John Doe", email="jdoe@example.com",
                   gpgkey="auto", label="fedora-yumrepos-19-x86_64",
                   repo_file_content="REPO_FILE_CONTENT", workdir=self.workdir)

        TT.gen_gpgkey(ctx, rpmmacros=os.path.join(self.workdir, "rpmmacros"),
                      homedir=self.workdir, compat=True, passphrase="secret")

    def test_110_run(self):
        repos = mk_local_repos(os.path.join(self.workdir, "yum"))
        ctx = mk_ctx(repos[:1])
        ctx["workdir"] = self.workdir

        self.assertTrue(TT.run(ctx))

        # FIXME: What should be done with the result to check its success ?
        reposrpms = glob.glob(os.path.join(self.workdir, "*.src.rpm"))

        self.assertTrue(reposrpms)
        self.assertEquals(len(reposrpms), 1)  # A srpm should exist.
        #self.assertTrue(MS.run("mock -r fedora-19-x86_64 " + reposrpms[0]))

    def test_112_run_multi_repos(self):
        repos = mk_local_repos(os.path.join(self.workdir, "yum"))
        ctx = mk_ctx(repos)
        ctx["workdir"] = self.workdir

        self.assertTrue(TT.run(ctx))

        # FIXME: Likewise
        reposrpms = glob.glob(os.path.join(self.workdir, "*.src.rpm"))

        self.assertTrue(reposrpms)
        self.assertEquals(len(reposrpms), 3)  # There are 3 repos.

        #for srpm in reposrpms:
        #    self.assertTrue(MS.run("mock -r fedora-19-x86_64 " + srpm))

    def test_120_run__w_gpgkey(self):
        repos = mk_local_repos(os.path.join(self.workdir, "yum"))
        ctx = mk_ctx(repos[:1])
        ctx["workdir"] = self.workdir

        keyids = _find_gpg_keyids()
        if keyids:
            ctx["keyid"] = keyid = random.choice(keyids)
        else:
            sys.stderr.write("No GPG keyid was found. Skip this test...\n")
            return

        self.assertTrue(TT.run(ctx))

        # FIXME: What should be done with the result to check its success ?
        reposrpms = glob.glob(os.path.join(self.workdir, "*.src.rpm"))

        self.assertTrue(reposrpms)
        self.assertEquals(len(reposrpms), 1)  # A srpm should exist.
        #self.assertTrue(MS.run("mock -r fedora-19-x86_64 " + reposrpms[0]))

    def test_200_run__deploy(self):
        topdir = os.path.join(self.workdir, "yum")
        repos = mk_local_repos(topdir)
        ctx = mk_ctx(repos[:1])
        ctx["workdir"] = self.workdir
        ctx["deploy"] = True

        repo = repos[0]

        # ensure dirs to deploy rpms exists:
        rpmdirs = [os.path.join(repo.destdir, a) for a
                   in repo.archs + ["sources"]]

        for d in rpmdirs:
            os.makedirs(d)

        self.assertTrue(TT.run(ctx))

        def _list_rpms(d, pat="*.src.rpm"):
            return glob.glob(os.path.join(d, pat))

        srpms = _list_rpms(self.workdir)
        self.assertTrue(srpms)
        self.assertEquals(len(srpms), 1)  # A srpm should exist.
        srpm = Srpm(srpms[0])
        srpm.resolve()

        for d in rpmdirs:
            rpms = _list_rpms(d, "*.rpm")
            self.assertTrue(rpms)

    def test_202_run__deploy_w_gpgkey(self):
        topdir = os.path.join(self.workdir, "yum")
        repos = mk_local_repos(topdir)
        ctx = mk_ctx(repos[:1])
        ctx["workdir"] = self.workdir
        ctx["deploy"] = True

        repo = repos[0]

        # ensure dirs to deploy rpms exists:
        rpmdirs = [os.path.join(repo.destdir, a) for a
                   in repo.archs + ["sources"]]

        for d in rpmdirs:
            os.makedirs(d)

        keyids = _find_gpg_keyids()
        if keyids:
            ctx["keyid"] = keyid = random.choice(keyids)
        else:
            sys.stderr.write("No GPG keyid was found. Skip this test...\n")
            return

        self.assertTrue(TT.run(ctx))

        def _list_rpms(d, pat="*.src.rpm"):
            return glob.glob(os.path.join(d, pat))

        srpms = _list_rpms(self.workdir)
        self.assertTrue(srpms)
        self.assertEquals(len(srpms), 1)  # A srpm should exist.
        srpm = Srpm(srpms[0])
        srpm.resolve()

        for d in rpmdirs:
            rpms = _list_rpms(d, "*.rpm")
            self.assertTrue(rpms)

# vim:sw=4:ts=4:et:
