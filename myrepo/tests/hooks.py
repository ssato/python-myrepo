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
import myrepo.hooks as H
import myrepo.plugin as P
import myrepo.tests.common as TC

import os
import os.path
import sys
import unittest


def init(*args, **kwargs):
    print >> sys.stderr, "called init()"


def get_module(name="00_plugin", mdir=TC.selfdir()):
    return P._load_module(name, mdir)


class Test_00_find_hook(unittest.TestCase):

    def test_00_find_hook__pre(self):
        g = H.find_hook(init, "pre_", get_module())

        self.assertEquals(type(g), type(init))  # is g function?
        self.assertNotEquals(g, H.noop)

        g()

    def test_10_find_hook__post(self):
        g = H.find_hook(init, "post_", get_module())

        self.assertEquals(type(g), type(init))
        self.assertNotEquals(g, H.noop)

        g()


class Test_10_hook(unittest.TestCase):

    def setUp(self):
        self.workdir = TC.setup_workdir()

    def tearDown(self):
        TC.cleanup_workdir(self.workdir)

    def test_00_hook__w_all_parameters(self):
        g = H.hook(init, [get_module()], False, "pre_", "post_")
        g()


# vim:sw=4:ts=4:et:
