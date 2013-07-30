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

import os.path
import time
import unittest


class Test_00(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

        (s, u) = ("localhost", "jdoe")
        (dn, dv, _) = C.sample_base_dist().split("-")
        n = "%s-custom" % dn
        bdist = "%s-%s-%s" % (n, dv, "x86_64")
        archs = ["x86_64", "i386"]

        self.repo = R.Repo(s, u, dn, dv, archs, n,
                           subdir="yum", topdir=self.workdir,
                           baseurl="file://%(topdir)s", bdist=bdist)

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_00_init__no_genconf(self):
        ctx = dict(repo=self.repo)
        ctx["genconf"] = False

        self.assertTrue(TT.init(ctx))
        time.sleep(3)  # FIXME: Why this is needed?

        for d in self.repo.rpmdirs:
            self.assertTrue(os.path.exists(d), d)

    def test_30_init_and_update(self):
        ctx = dict(repo=self.repo)
        ctx["genconf"] = False

        self.assertTrue(TT.init(ctx))
        time.sleep(3)  # FIXME: Why this is needed?

        self.assertTrue(TT.update(ctx))


# vim:sw=4:ts=4:et:
