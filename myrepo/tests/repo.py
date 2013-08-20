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
import myrepo.genconf as MG
import myrepo.tests.common as C

import logging
import os.path
import unittest


class Test_30_classes(unittest.TestCase):

    def test_10__Server__init__(self):
        s = TT.Server("localhost.localdomain", "jdoe", baseurl="file:///tmp")

        self.assertEquals(s.name, "localhost.localdomain")
        self.assertEquals(s.altname, "localhost.localdomain")
        self.assertEquals(s.shortname, "localhost")
        self.assertEquals(s.shortaltname, "localhost")
        self.assertEquals(s.user, "jdoe")
        self.assertEquals(s.baseurl, "file:///tmp")

        self.assertEquals(s.deploy_cmd("/tmp/a", "/b/c/d"),
                          "cp -a /tmp/a /b/c/d")

    def test_12__Server__init__(self):
        s = TT.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")

        self.assertEquals(s.name, "yumrepos-1.local")
        self.assertEquals(s.altname, "yumrepos.example.com")
        self.assertEquals(s.shortname, "yumrepos-1")
        self.assertEquals(s.shortaltname, "yumrepos")
        self.assertEquals(s.user, "jdoe")
        self.assertEquals(s.baseurl, "http://yumrepos.example.com/~jdoe/yum")

        self.assertEquals(s.deploy_cmd("/tmp/a", "/b/c/d"),
                          "scp -p /tmp/a jdoe@yumrepos-1.local:/b/c/d")

    def test_20__Dict__init__(self):
        d = TT.Dist("fedora-19", "x86_64")

        self.assertTrue(isinstance(d, TT.Dist))

        self.assertEquals(d.dist, "fedora-19")
        self.assertEquals(d.arch, "x86_64")
        self.assertEquals(d.label, "fedora-19-x86_64")
        self.assertEquals(d.mockcfg, "fedora-19-x86_64.cfg")
        self.assertEquals(d.rpmdir(), "/var/lib/mock/fedora-19-x86_64/result")

    def test_30__Repo__init__(self):
        server = TT.Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
        repo = TT.Repo("fedora", 19, ["x86_64", "i386"], server,
                       "%(name)s-%(server_shortaltname)s")

        self.assertTrue(isinstance(repo, TT.Repo))

        self.assertEquals(repo.name, "fedora")
        self.assertEquals(repo.version, "19")
        self.assertEquals(repo.archs, ["x86_64", "i386"])
        self.assertEquals(repo.server_name, "yumrepos-1.local")
        self.assertEquals(repo.server_altname, "yumrepos.example.com")
        self.assertEquals(repo.server_shortname, "yumrepos-1")
        self.assertEquals(repo.server_shortaltname, "yumrepos")
        self.assertEquals(repo.server_baseurl,
                          "http://yumrepos.example.com/~jdoe/yum")
        self.assertTrue(repo.multiarch)
        self.assertEquals(repo.primary_arch, "x86_64")
        self.assertEquals(repo.dist, "fedora-19")
        self.assertEquals(repo.subdir, "fedora/19")
        self.assertEquals(repo.destdir, "~jdoe/public_html/yum/fedora/19")
        self.assertEquals(repo.baseurl,
                          "http://yumrepos.example.com/~jdoe/yum")
        self.assertEquals(repo.rpmdirs,
                          ["~jdoe/public_html/yum/fedora/19/sources",
                           "~jdoe/public_html/yum/fedora/19/x86_64",
                           "~jdoe/public_html/yum/fedora/19/i386"])
        self.assertEquals(repo.reponame, "fedora-yumrepos")


# vim:sw=4:ts=4:et:
