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
import myrepo.cmds as TT
import myrepo.repo as MR
import myrepo.tests.common as C

import logging
import os.path
import unittest


_REMOTE_REPO_0 = MR.Repo("fedora", 19, ["x86_64", "i386"],
                         MR.Server("yumrepos-1.local", "jdoe"))


class Test_10(unittest.TestCase):

    def test_10_mk_cmds_to_build_srpm__noarch(self):
        repo = _REMOTE_REPO_0
        srpm = "/tmp/abc-0.0.1-1.src.rpm"  # dummy

        logging.getLogger().setLevel(logging.INFO)
        cs = TT.mk_cmds_to_build_srpm(repo, srpm, True)

        self.assertTrue(cs)
        self.assertTrue(len(cs) == 1)
        self.assertEquals(cs[0], "mock -r fedora-19-x86_64 " + srpm)

    def test_12_mk_cmds_to_build_srpm__arch(self):
        repo = _REMOTE_REPO_0
        srpm = "/tmp/abc-0.0.1-1.src.rpm"  # dummy

        logging.getLogger().setLevel(logging.INFO)
        cs = TT.mk_cmds_to_build_srpm(repo, srpm, False)

        self.assertTrue(cs)
        self.assertTrue(len(cs) == 2)
        self.assertEquals(cs[0], "mock -r fedora-19-x86_64 " + srpm)
        self.assertEquals(cs[1], "mock -r fedora-19-i386 " + srpm)

    def test_14_mk_cmds_to_build_srpm__noarch_bdist(self):
        repo = _REMOTE_REPO_0
        srpm = "/tmp/abc-0.0.1-1.src.rpm"  # dummy
        bdist = "fecora-yumrepos-19"

        logging.getLogger().setLevel(logging.INFO)
        cs = TT.mk_cmds_to_build_srpm(repo, srpm, True, bdist)

        self.assertTrue(cs)
        self.assertTrue(len(cs) == 1)
        self.assertEquals(cs[0], "mock -r %s-x86_64 %s" % (bdist, srpm))

    def test_16_mk_cmds_to_build_srpm__arch_bdist(self):
        repo = _REMOTE_REPO_0
        srpm = "/tmp/abc-0.0.1-1.src.rpm"  # dummy
        bdist = "fecora-yumrepos-19"

        logging.getLogger().setLevel(logging.INFO)
        cs = TT.mk_cmds_to_build_srpm(repo, srpm, False, bdist)

        self.assertTrue(cs)
        self.assertTrue(len(cs) == 2)
        self.assertEquals(cs[0], "mock -r %s-x86_64 %s" % (bdist, srpm))
        self.assertEquals(cs[1], "mock -r %s-i386 %s" % (bdist, srpm))

    def test_20_mk_cmds_to_deploy_rpms__noarch(self):
        repo = _REMOTE_REPO_0
        srpm = "/tmp/abc-0.0.1-1.src.rpm"  # dummy
        ref = [
            "scp -p /var/lib/mock/fedora-19-x86_64/result/*.src.rpm " +
            "jdoe@yumrepos-1.local:~jdoe/public_html/yum/fedora/19/sources",
            "scp -p /var/lib/mock/fedora-19-x86_64/result/*.noarch.rpm " +
            "jdoe@yumrepos-1.local:~jdoe/public_html/yum/fedora/19/x86_64" +
            " && ssh -o ConnectTimeout=10 jdoe@yumrepos-1.local " +
            "'cd ~jdoe/public_html/yum/fedora/19 && " +
            "for arch in i386; do (cd $arch/ && "
            "(for f in ../x86_64/*.noarch.rpm; do ln -sf $f ./; done)); " +
            "done'"
        ]
        cs = TT.mk_cmds_to_deploy_rpms(repo, srpm, True)

        self.assertTrue(cs)
        self.assertTrue(len(cs) == 2)
        self.assertEquals(cs[0], ref[0])
        self.assertEquals(cs[1], ref[1])

    def test_22_mk_cmds_to_deploy_rpms__arch(self):
        repo = _REMOTE_REPO_0
        srpm = "/tmp/abc-0.0.1-1.src.rpm"  # dummy
        ref = [
            "scp -p /var/lib/mock/fedora-19-x86_64/result/*.src.rpm " +
            "jdoe@yumrepos-1.local:~jdoe/public_html/yum/fedora/19/sources",
            "scp -p /var/lib/mock/fedora-19-x86_64/result/*.x86_64.rpm " +
            "jdoe@yumrepos-1.local:~jdoe/public_html/yum/fedora/19/x86_64",
            "scp -p /var/lib/mock/fedora-19-i386/result/*.i386.rpm " +
            "jdoe@yumrepos-1.local:~jdoe/public_html/yum/fedora/19/i386"
        ]
        cs = TT.mk_cmds_to_deploy_rpms(repo, srpm, False)

        self.assertTrue(cs)
        self.assertTrue(len(cs) == 3)
        self.assertEquals(cs[0], ref[0])
        self.assertEquals(cs[1], ref[1])
        self.assertEquals(cs[2], ref[2])

    def test_24_mk_cmds_to_deploy_rpms__noarch_bdist(self):
        repo = _REMOTE_REPO_0
        srpm = "/tmp/abc-0.0.1-1.src.rpm"  # dummy
        bdist = "fecora-yumrepos-19"
        ref = [
            "scp -p /var/lib/mock/%s-x86_64/result/*.src.rpm " % bdist +
            "jdoe@yumrepos-1.local:~jdoe/public_html/yum/fedora/19/sources",
            "scp -p /var/lib/mock/%s-x86_64/result/*.noarch.rpm " % bdist +
            "jdoe@yumrepos-1.local:~jdoe/public_html/yum/fedora/19/x86_64" +
            " && ssh -o ConnectTimeout=10 jdoe@yumrepos-1.local " +
            "'cd ~jdoe/public_html/yum/fedora/19 && " +
            "for arch in i386; do (cd $arch/ && "
            "(for f in ../x86_64/*.noarch.rpm; do ln -sf $f ./; done)); " +
            "done'"
        ]
        cs = TT.mk_cmds_to_deploy_rpms(repo, srpm, True, bdist)

        self.assertTrue(cs)
        self.assertTrue(len(cs) == 2)
        self.assertEquals(cs[0], ref[0])
        self.assertEquals(cs[1], ref[1])

    def test_26_mk_cmds_to_deploy_rpms__arch_bdist(self):
        repo = _REMOTE_REPO_0
        srpm = "/tmp/abc-0.0.1-1.src.rpm"  # dummy
        bdist = "fecora-yumrepos-19"
        ref = [
            "scp -p /var/lib/mock/%s-x86_64/result/*.src.rpm " % bdist +
            "jdoe@yumrepos-1.local:~jdoe/public_html/yum/fedora/19/sources",
            "scp -p /var/lib/mock/%s-x86_64/result/*.x86_64.rpm " % bdist +
            "jdoe@yumrepos-1.local:~jdoe/public_html/yum/fedora/19/x86_64",
            "scp -p /var/lib/mock/%s-i386/result/*.i386.rpm " % bdist +
            "jdoe@yumrepos-1.local:~jdoe/public_html/yum/fedora/19/i386"
        ]
        cs = TT.mk_cmds_to_deploy_rpms(repo, srpm, False, bdist)

        self.assertTrue(cs)
        self.assertTrue(len(cs) == 3)
        self.assertEquals(cs[0], ref[0])
        self.assertEquals(cs[1], ref[1])
        self.assertEquals(cs[2], ref[2])

    def test_30_mk_cmds_to_update(self):
        repo = _REMOTE_REPO_0
        ref = [
            "ssh -o ConnectTimeout=10 jdoe@yumrepos-1.local " +
            "'cd ~jdoe/public_html/yum/fedora/19/x86_64 && " +
            TT._UPDATE_REPO_METADATA + "'",
            "ssh -o ConnectTimeout=10 jdoe@yumrepos-1.local " +
            "'cd ~jdoe/public_html/yum/fedora/19/i386 && " +
            TT._UPDATE_REPO_METADATA + "'"
        ]
        cs = TT.mk_cmds_to_update(repo)

        self.assertTrue(cs)
        self.assertTrue(len(cs) == 2)
        self.assertEquals(cs[0], ref[0])
        self.assertEquals(cs[1], ref[1])

    def test_40_mk_cmds_to_update(self):
        repo = _REMOTE_REPO_0
        ref = [
            "ssh -o ConnectTimeout=10 jdoe@yumrepos-1.local " +
            "'mkdir -p ~jdoe/public_html/yum/fedora/19/{x86_64,i386,sources}'"
        ]
        cs = TT.mk_cmds_to_init__no_genconf(repo)

        self.assertTrue(cs)
        self.assertTrue(len(cs) == 1)
        self.assertEquals(cs[0], ref[0])


# vim:sw=4:ts=4:et:
