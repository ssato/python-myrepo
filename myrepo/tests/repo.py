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
        server = TT.RepoServer("yumrepos.local", "jdoe",
                               "yumrepos.example.com")

        repo = TT.Repo("%(base_name)s-%(server_shortname)s-%(server_user)s",
                       19, ["x86_64", "i386"], "fedora", server)

        self.assertTrue(isinstance(repo, TT.Repo))

        self.assertEquals(repo.version, "19")
        self.assertEquals(repo.archs, ["x86_64", "i386"])
        self.assertEquals(repo.base_name, "fedora")
        self.assertEquals(repo.server_name, "yumrepos.local")
        self.assertEquals(repo.server_altname, "yumrepos.example.com")
        self.assertEquals(repo.server_shortname, "yumrepos")
        self.assertEquals(repo.server_baseurl,
                          "http://yumrepos.example.com/~jdoe/yum")
        self.assertTrue(repo.multiarch)
        self.assertEquals(repo.primary_arch, "x86_64")
        self.assertEquals(repo.base_dist, "fedora-19")
        self.assertEquals(repo.base_label, "fedora-19-x86_64")
        self.assertEquals(repo.distdir, "fedora/19")
        self.assertEquals(repo.destdir, "~jdoe/public_html/yum/fedora/19")
        self.assertEquals(repo.baseurl,
                          "http://yumrepos.example.com/~jdoe/yum/fedora/19/")
        self.assertEquals(repo.rpmdirs,
                          ["~jdoe/public_html/yum/fedora/19/sources",
                           "~jdoe/public_html/yum/fedora/19/x86_64",
                           "~jdoe/public_html/yum/fedora/19/i386"])
        self.assertEquals(repo.name, "fedora-yumrepos-jdoe")
        self.assertEquals(repo.dist, "fedora-yumrepos-jdoe-19")
        self.assertEquals(repo.label, "fedora-yumrepos-jdoe-19-x86_64")
        self.assertEquals(repo.repofile, "fedora-yumrepos-jdoe-19.repo")

    def test_10__init__w_min_args(self):
        server = TT.RepoServer("yumrepos.local", "jdoe",
                               "yumrepos.example.com")

        repo = TT.Repo("fedora-custom", 19, ["x86_64", "i386"], "fedora",
                       server)

        self.assertTrue(isinstance(repo, TT.Repo))

        self.assertEquals(repo.version, "19")
        self.assertEquals(repo.archs, ["x86_64", "i386"])
        self.assertEquals(repo.base_name, "fedora")
        self.assertEquals(repo.server_name, "yumrepos.local")
        self.assertEquals(repo.server_altname, "yumrepos.example.com")
        self.assertEquals(repo.server_shortname, "yumrepos")
        self.assertEquals(repo.server_baseurl,
                          "http://yumrepos.example.com/~jdoe/yum")
        self.assertTrue(repo.multiarch)
        self.assertEquals(repo.primary_arch, "x86_64")
        self.assertEquals(repo.base_dist, "fedora-19")
        self.assertEquals(repo.base_label, "fedora-19-x86_64")
        self.assertEquals(repo.distdir, "fedora/19")
        self.assertEquals(repo.destdir, "~jdoe/public_html/yum/fedora/19")
        self.assertEquals(repo.baseurl,
                          "http://yumrepos.example.com/~jdoe/yum/fedora/19/")
        self.assertEquals(repo.rpmdirs,
                          ["~jdoe/public_html/yum/fedora/19/sources",
                           "~jdoe/public_html/yum/fedora/19/x86_64",
                           "~jdoe/public_html/yum/fedora/19/i386"])
        self.assertEquals(repo.name, "fedora-custom")
        self.assertEquals(repo.dist, "fedora-custom-19")
        self.assertEquals(repo.label, "fedora-custom-19-x86_64")
        self.assertEquals(repo.repofile, "fedora-custom-19.repo")

# vim:sw=4:ts=4:et:
