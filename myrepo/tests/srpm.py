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
import myrepo.srpm as TT
import myrepo.tests.common as C

import os.path
import os
import random
import subprocess
import unittest


def list_found_rpms(srpm=True, max=10):
    """
    List path of existing RPMs.

    FIXME: Very ugly and not safe.

    :param srpm: List source rpms if True else binary rpms.
    :param max: Max number of rpms to list

    :return: List of rpm paths or [].
    """
    pat = ".src.rpm" if srpm else ".noarch.rpm .x86_64.rpm .i386.rpm"
    try:
        o = subprocess.check_output("locate %s" % pat, shell=True)
        if o:
            rpms = o.split('\n')
            return [x for x in random.sample(rpms, max) if x.endswith(".rpm")
                    and os.path.exists(x) and os.access(x, os.R_OK)]

    except subprocess.CalledProcessError:
        pass

    return []


class Test_00_Srpm(unittest.TestCase):

    def test_00___init__(self):
        path = "/path/to/dummy/src.rpm"
        srpm = TT.Srpm(path)

        self.assertTrue(isinstance(srpm, TT.Srpm))

    def test_02___init___w_resolved(self):
        path = "/path/to/dummy/src.rpm"
        srpm = TT.Srpm(path, "foo", "1.0", "1", True, True, True)

        self.assertTrue(isinstance(srpm, TT.Srpm))
        self.assertTrue(srpm.resolved)

    def test_10_resolve__srpm_ok(self):
        path = random.choice(list_found_rpms())
        srpm = TT.Srpm(path)

        self.assertTrue(isinstance(srpm, TT.Srpm))

        srpm.resolve()

        self.assertTrue(srpm.is_srpm)
        self.assertTrue(srpm.resolved)

        self.assertNotEquals(srpm.name, None)
        self.assertNotEquals(srpm.version, None)
        self.assertNotEquals(srpm.release, None)
        self.assertNotEquals(srpm.noarch, None)


# vim:sw=4:ts=4:et:
