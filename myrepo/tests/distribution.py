#
# Copyright (C) 2012, 2013 Red Hat, Inc.
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
import myrepo.distribution as D
import rpmkit.environ as E

import random
import unittest


def sample_dist():
    return random.choice(E.list_dists())


def is_base_dist(dist):
    """
    Fixme: Ugly

    >>> is_base_dist("fedora-16-i386")
    True
    >>> is_base_dist("rhel-6-x86_64")
    True
    >>> is_base_dist("fedora-xyz-extras-fedora-16-x86_64")
    False
    """
    return len(dist.split("-")) == 3


def sample_base_dist():
    return random.choice([d for d in E.list_dists() if is_base_dist(d)])


class Test_00(unittest.TestCase):

    def test_10__build_cmd(self):
        bdist = sample_dist()
        c = D._build_cmd(bdist, "foo-x.y.z.src.rpm")
        self.assertTrue(isinstance(c, str))
        self.assertNotEquals(c, "")


class Test_10_Distribution(unittest.TestCase):

    def test_00__init__w_min_args(self):
        (n, v, a) = sample_base_dist().split("-")
        d = D.Distribution(n, v, a)

        self.assertTrue(isinstance(d, D.Distribution))

        self.assertEquals(d.name, n)
        self.assertEquals(d.version, v)
        self.assertEquals(d.arch, a)
        self.assertEquals(d.dist, "%s-%s" % (n, v))
        self.assertEquals(d.label, "%s-%s-%s" % (n, v, a))
        self.assertEquals(d.bdist, "%s-%s" % (n, v))

        blabel = "%s-%s-%s" % (n, v, a)
        self.assertEquals(d.blabel, blabel)

        self.assertEquals(d.get_mockcfg_path(), "/etc/mock/%s.cfg" % blabel)
        self.assertEquals(d.rpmdir(), "/var/lib/mock/%s/result" % blabel)

    def test_05__init__w_bdist(self):
        (n, v, a) = sample_base_dist().split("-")
        bdist = "%s-custom-%s-%s" % (n, v, a)

        d = D.Distribution(n, v, a, bdist)
        self.assertTrue(isinstance(d, D.Distribution))

        self.assertEquals(d.name, n)
        self.assertEquals(d.version, v)
        self.assertEquals(d.arch, a)
        self.assertEquals(d.dist, "%s-%s" % (n, v))
        self.assertEquals(d.label, "%s-%s-%s" % (n, v, a))
        self.assertEquals(d.bdist, bdist)

        blabel = "%s-%s" % (bdist, a)
        self.assertEquals(d.blabel, blabel)

        self.assertEquals(d.get_mockcfg_path(), "/etc/mock/%s.cfg" % blabel)
        self.assertEquals(d.rpmdir(), "/var/lib/mock/%s/result" % blabel)

# vim:sw=4:ts=4:et:
