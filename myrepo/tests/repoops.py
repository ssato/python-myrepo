#
# Copyright (C) 2012 Red Hat, Inc.
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
import myrepo.repoops as TT
import myrepo.distribution as D
import myrepo.tests.common as C

import difflib
import os.path
import unittest


_CURDIR = C.selfdir()
_TPATHS = [os.path.join(_CURDIR, "../../templates/2"), ]

_DIST_0 = D.Distribution("fedora", "19", "x86_64", "fedora-custom-19")
_DIST_1 = D.Distribution("fedora", "19", "i386", "fedora-custom-19")

_REPO_0 = dict(name="fedora-custom-19-x86_64",
               server="yumrepo.example.com",
               user="jdoe",
               baseurl="http://yumrepo.example.com/yum/fedora/19/",
               dist="fedora-custom-19",
               dists=[_DIST_0, _DIST_1],
               distversion=19)


def diff(s, ref):
    return "\n'" + "\n".join(difflib.unified_diff(s.splitlines(),
                                                  ref.splitlines(),
                                                  'Result', 'Expected')) + "'"


def readfile(f):
    return open(os.path.join(_CURDIR, f)).read()


class Test_00(unittest.TestCase):

    def test_10_gen_repo_file_content(self):
        ref = readfile("result.repo.0")
        s = TT.gen_repo_file_content(_REPO_0, _TPATHS)

        self.assertEquals(s, ref, diff(s, ref))

    def test_20_gen_mock_cfg_content(self):
        ref = readfile("result.mock.cfg.0").replace("REPO_FILE_CONTENT",
                                                    readfile("result.repo.0"))

        s = TT.gen_mock_cfg_content(_REPO_0,  _DIST_0, _TPATHS)

        self.assertEquals(s, ref, diff(s, ref))

    def test_30_gen_rpmspec_content(self):
        datestamp = TT.datestamp()
        ref = readfile("result.yum-repodata.spec.0").replace("DATESTAMP",
                                                             datestamp)

        ctx = dict(repo=_REPO_0, version="0.0.1", datestamp=datestamp,
                   fullname="John Doe", email="jdoe@example.com")

        s = TT.gen_rpmspec_content(ctx, _TPATHS)

        self.assertEquals(s, ref, diff(s, ref))

    def test_40_sign_rpms_cmd(self):
        """TODO: test cases for sign_rpm_cmd()"""
        return

        ref = readfile("result.sign_rpms.0")
        s = TT.sign_rpms_cmd("XYZ01234", ["aaa-0.1-1.noarch.rpm",
                                          "aaa-bbb-0.1-1.noarch.rpm",
                                          "aaa-ccc-0.1-1.noarch.rpm"])

        self.assertEquals(s, ref, diff(s, ref))

    def test_50_mock_cfg_paths_and_contents_g(self):
        mcs = list(TT.mock_cfg_paths_and_contents_g(_REPO_0, "/tmp", _TPATHS))
        self.assertEquals(mcs[0][0],
                          "/tmp/etc/mock/fedora-custom-19-x86_64.cfg")
        self.assertEquals(mcs[1][0],
                          "/tmp/etc/mock/fedora-custom-19-i386.cfg")

    def test_60_rpm_build_cmd(self):
        ref = readfile("result.rpmbuild.0")

        ctx = dict(repo=_REPO_0, workdir="/tmp/w", fullname="John Doe",
                   email="jdoe@example.com", listfile="a b c", logopt="-v")

        s = TT.rpm_build_cmd(ctx, "/tmp/w", "fedora-custom-19-release",
                             "a b c", _TPATHS)

        self.assertEquals(s, ref, diff(s, ref))


class Test_10(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_10_gen_repo_file(self):
        path = TT.gen_repo_file(_REPO_0, self.workdir, _TPATHS)

        self.assertTrue(os.path.exists(path))
        self.assertTrue(os.path.isfile(path))

        ref = readfile("result.repo.0")
        s = open(path).read()

        self.assertEquals(s, ref, diff(s, ref))


# vim:sw=4:ts=4:et:
