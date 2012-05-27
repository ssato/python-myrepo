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
import myrepo.config as C
import myrepo.utils as U
import rpmkit.Bunch as B

import unittest


class Test_00(unittest.TestCase):

    def test__init_by_defaults(self):
        cfg = C._init_by_defaults()
        U.typecheck(cfg, B.Bunch)

    def test__init_by_config_file__wo_config_file(self):
        cfg = C._init_by_config_file()
        U.typecheck(cfg, B.Bunch)


# vim:sw=4:ts=4:et:
