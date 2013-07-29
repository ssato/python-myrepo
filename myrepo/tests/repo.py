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
import myrepo.repo as TT
import myrepo.tests.common as C

import unittest


class Test_00(unittest.TestCase):

    def test_00__init__w_min_args(self):
        (s, u) = ("localhost.localdomain", "jdoe")
        (dn, dv, _) = C.sample_base_dist().split("-")
        n = "%s-custom" % dn
        bdist = "%s-%s-%s" % (n, dv, "x86_64")
        archs = ["x86_64", "i386"]

        repo = TT.Repo(s, u, dn, dv, archs, n, bdist=bdist)

        self.assertTrue(isinstance(repo, TT.Repo))

        self.assertEquals(repo.server, s)
        self.assertEquals(repo.user, u)
        self.assertEquals(repo.archs, archs)
        self.assertEquals(repo.hostname, "localhost")
        self.assertTrue(repo.multiarch)
        self.assertEquals(repo.primary_arch, "x86_64")
        self.assertEquals(repo.distname, dn)
        self.assertEquals(repo.distversion, dv)
        self.assertEquals(repo.dist, "%s-%s" % (dn, dv))
        self.assertEquals(repo.bdist, bdist)


# vim:sw=4:ts=4:et:
