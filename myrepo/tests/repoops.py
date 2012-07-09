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
import myrepo.repoops as RO
import unittest


class Test_00(unittest.TestCase):

    def test_00_is_noarch(self):
        """TODO: implement tests for is_noarch"""
        pass

    def test_10_dists_by_srpm(self):
        """TODO: implement tests for dists_by_srpm"""
        pass

    def test_20_release_file_content(self):
        """TODO: implement tests for release_file_content"""
        pass

    def test_30_mock_cfg_content(self):
        """TODO: implement tests for mock_cfg_content"""
        pass

    def test_40_mock_cfg_content_2(self):
        """TODO: implement tests for mock_cfg_content_2"""
        pass

    def test_50_sign_rpms_cmd(self):
        """TODO: implement tests for sign_rpms_cmd"""
        pass

    def test_60_copy_cmd(self):
        """TODO: implement tests for copy_cmd"""
        pass

    def test_70_release_file_gen(self):
        """TODO: implement tests for release_file_gen"""
        pass

    def test_80_mock_cfg_gen(self):
        """TODO: implement tests for mock_cfg_gen"""
        pass


class Test_10_build(unittest.TestCase):

    def test_00_build(self):
        """TODO: implement tests for build"""
        pass

    def test_10_update_metadata(self):
        """TODO: implement tests for update_metadata"""
        pass

    def test_20_build_mock_cfg_srpm(self):
        """TODO: implement tests for build_mock_cfg_srpm"""
        pass

    def test_30_build_release_srpm(self):
        """TODO: implement tests for build_release_srpm"""
        pass


# vim:sw=4:ts=4:et:
