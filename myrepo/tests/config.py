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
import myrepo.config as TT
import myrepo.tests.common as C

import os
import os.path
import unittest


_CONF_KEYS = ("dists", "dists_full", "dist_choices", "tpaths",
              "workdir", "verbosity", "config", "profile",
              "hostname", "altname", "user", "topdir", "baseurl",
              "timeout", "genconf", "fullname", "email", "keyid",
              "repo_params", "sign", "selfref")

_CONF_0 = """\
[DEFAULT]
# The followings are site-local convention and DO NOT EDIT:
hostname: yumrepos.example.local
altname: yumrepos.example.com
email: %(user)s@example.com
reponame: %(basename)s-com-example-%(user)s

# Customize the followings as needed:
#user: jdoe
#fullname: John Doe
dists: fedora-19-x86_64,fedora-19-i386,rhel-6-x86_64
"""


class Test_00(unittest.TestCase):

    def test_10__init_by_preset_defaults(self):
        cfg = TT._init_by_preset_defaults()
        self.assertTrue(isinstance(cfg, dict))

        # This check is far from perfect but...
        for k in _CONF_KEYS:
            self.assertTrue(k in cfg)

        self.assertTrue(isinstance(cfg["repo_params"], list))


class Test_10(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()
        self.conf = os.path.join(self.workdir, "00.conf")

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_10__init_by_config__w_config_file(self):
        open(self.conf, 'w').write(_CONF_0)

        cfg = TT._init_by_config(self.conf)
        self.assertTrue(isinstance(cfg, dict))

        for k in ("hostname", "email", "reponame", "dists"):
            self.assertTrue(k in cfg, "k=" + k)

    def test_12__init_by_config__w_config_files_in_dir(self):
        confdir = os.path.join(self.workdir, "conf.d")
        os.makedirs(confdir)
        open(os.path.join(confdir, "00.conf"), 'w').write(_CONF_0)

        cfg = TT._init_by_config(confdir)
        self.assertTrue(isinstance(cfg, dict))

        for k in ("hostname", "email", "reponame", "dists"):
            self.assertTrue(k in cfg, "k=" + k)

    def test_20_init___w_config_file(self):
        open(self.conf, 'w').write(_CONF_0)

        cfg = TT.init(self.conf)
        self.assertTrue(isinstance(cfg, dict))

        for k in _CONF_KEYS:
            self.assertTrue(k in cfg)

        self.assertEquals(cfg["hostname"], "yumrepos.example.local")
        self.assertEquals(cfg["altname"], "yumrepos.example.com")
        self.assertEquals(cfg["dists"],
                          "fedora-19-x86_64,fedora-19-i386,rhel-6-x86_64")

    def test_30_opt_parser___w_config_file(self):
        open(self.conf, 'w').write(_CONF_0)

        p = TT.opt_parser(self.conf)
        self.assertTrue(isinstance(p, TT.optparse.OptionParser))

# vim:sw=4:ts=4:et:
