#
# Copyright (C) 2012, 2013 Red Hat, Inc.
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
import myrepo.utils as U

import difflib
import os
import os.path
import sys
import unittest


TESTDIR = os.path.dirname(__file__)
TEMPLATE_PATH = os.path.abspath(os.path.join(TESTDIR, ".."))
MOCK_BUILD_DIR = "/var/cache/mock/fedora-18-x86_64"


def tcompile(tmpl_name, ctx):
    return U.compile_template_2(tmpl_name, ctx, [TEMPLATE_PATH])


def expected_s(tmpl_name):
    return open(os.path.join(TESTDIR, tmpl_name)).read()


def trim(s):
    return s.rstrip().strip()


def result_and_expected(tmpl_name, ctx, dump=False,
                        dumpdir="/tmp/myrepo-templates-out"):
    s = trim(tcompile(tmpl_name, ctx))
    exp_s = trim(expected_s(tmpl_name))

    if dump:
        if not os.path.exists(dumpdir):
            os.makedirs(dumpdir)

        open(os.path.join(dumpdir, tmpl_name), 'w').write(s)

    return (trim(s), trim(exp_s))


def diff(s, ref):
    return "\n" + "".join(difflib.unified_diff(s.splitlines(),
                                               ref.splitlines(),
                                               'Original', 'Current'))


class Test_2(unittest.TestCase):

    def test_00_list_rpms_to_gc_py(self):
        ctx = dict(rpmsdir=os.path.join(MOCK_BUILD_DIR,
                                        "yum_cache/fedora/packages/"))
        (s, ref) = result_and_expected("list_rpms_to_gc.py", ctx, True)
        self.assertEquals(s, ref, diff(s, ref))

    def test_01_mock_cfg(self):
        ctx = dict(base_mock_cfg_path="/etc/mock/fedora-18-x86_64.cfg",
                   repo=dict(name="custom"),
                   dist=dict(label="fedora-18-x86_64",
                             name="fedora"),
                   release_file_content="HERE_IS_RELEASE_FILE_CONTENT")

        (s, ref) = result_and_expected("mock.cfg", ctx, True)
        self.assertEquals(s, ref, diff(s, ref))

    def test_02_mock_cfg_build(self):
        ctx = dict(name="custom-fedora-18-x86_64",
                   workdir="/tmp/w",
                   baseurl="http://yumrepo.example.com/yum/fedora/18/",
                   fullname="John Doe",
                   email="jdoe@example.com",
                   distversion=18,
                   listfile="a b c")

        (s, ref) = result_and_expected("mock_cfg_build", ctx, True)
        self.assertEquals(s, ref, diff(s, ref))

    def test_03_release_file(self):
        ctx = dict(name="custom-fedora-18-x86_64",
                   server="yumrepo.example.com",
                   user="jdoe",
                   baseurl="http://yumrepo.example.com/yum/fedora/18/",
                   metadata_expire=2,
                   signkey=False)

        (s, ref) = result_and_expected("release_file", ctx, True)
        self.assertEquals(s, ref, diff(s, ref))

    def test_04_release_file_build(self):
        ctx = dict(name="custom-fedora-18-x86_64",
                   workdir="/tmp/w",
                   baseurl="http://yumrepo.example.com/yum/fedora/18/",
                   fullname="John Doe",
                   email="jdoe@example.com",
                   distversion=18,
                   listfile="a b c",
                   logopt="-v")

        (s, ref) = result_and_expected("release_file_build", ctx, True)
        self.assertEquals(s, ref, diff(s, ref))

    def test_05_rpmbuild(self):
        ctx = dict(name="custom-fedora-18-x86_64",
                   workdir="/tmp/w",
                   baseurl="http://yumrepo.example.com/yum/fedora/18/",
                   fullname="John Doe",
                   email="jdoe@example.com",
                   distversion=18,
                   listfile="a b c",
                   logopt="-v")

        (s, ref) = result_and_expected("rpmbuild", ctx, True)
        self.assertEquals(s, ref, diff(s, ref))

    def test_06_sign_rpms(self):
        ctx = dict(keyid="XYZ01234",
                   rpms=["aaa-0.1-1.noarch.rpm",
                         "aaa-bbb-0.1-1.noarch.rpm",
                         "aaa-ccc-0.1-1.noarch.rpm"])

        (s, ref) = result_and_expected("sign_rpms", ctx, True)
        self.assertEquals(s, ref, diff(s, ref))

# vim:sw=4:ts=4:et:
