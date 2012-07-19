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
import myrepo.plugin as MP
import myrepo.tests.common as TC

import glob
import os
import os.path
import shutil
import unittest


class Test_00_pure_functions(unittest.TestCase):

    def test_00_selfdir(self):
        """TODO: Implement tests for selfdir()"""
        pass

    def test_10_pluginsdir__wo_args(self):
        """TODO: Implement tests for pluginsdir()"""
        pass

    def test_11_pluginsdir__w_base_arg(self):
        self.assertEquals(
            MP.pluginsdir("/a/b", MP.PLUGINS_SUBDIR),
            os.path.join("/a/b/", MP.PLUGINS_SUBDIR)
        )


class Test_10_effecful_functions(unittest.TestCase):

    def setUp(self):
        self.workdir = TC.setup_workdir()

    def tearDown(self):
        #TC.cleanup_workdir(self.workdir)
        pass

    def test_00_find_plugin_modules__w_pluginsdir(self):
        srcs = glob.glob(
            os.path.join(TC.selfdir(), MP.PLUGINS_FILENAME_PATTERN)
        )
        dst = os.path.join(self.workdir, MP.PLUGINS_SUBDIR)

        if not os.path.exists(dst):
            os.makedirs(dst)

        for f in srcs:
            shutil.copy(f, dst)

        basenames = [os.path.basename(os.path.splitext(f)[0]) for f in srcs]
        refs = sorted("%s.%s" % (MP.PLUGINS_PREFIX, n) for n in basenames)

        self.assertEquals(
            sorted(MP.find_plugin_modules(dst, MP.PLUGINS_PREFIX)),
            refs
        )


# vim:sw=4:ts=4:et:
