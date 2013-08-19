#
# Copyright (C) 2011 - 2013 Red Hat, Inc.
# Red Hat Author(s): Satoru SATOH <ssato@redhat.com>
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import myrepo.repo as MR
import myrepo.shell as SH
import rpmkit.rpmutils as RU

import logging
import os.path


def mk_cmds_to_build_srpm(repo, srpm, noarch=None, bdist=None):
    """
    Make up list of command strings to build given srpm.

    :param repo: Repo instance
    :param srpm: srpm path
    :param noarch: True or False if built RPM is noarch/arch-dependent and None
        if it's unknown
    :param bdist: Build dist (name-version), e.g. 'fedora-custom-19'

    :return: List of commands to build given srpm
    """
    assert isinstance(repo, MR.Repo), "Wrong arg repo of type " + repr(repo)

    if noarch is None:
        noarch = RU.is_noarch(srpm)

    if bdist is None:
        bdist = repo.dist

    if noarch:
        label = "%s-%s" % (bdist, repo.primary_arch)
        return [MR._build_cmd(label, srpm)]
    else:
        return [MR._build_cmd("%s-%s" % (bdist, a), srpm) for a in repo.archs]


_MK_SYMLINKS_TO_NOARCH_RPM = """\
for arch in %(other_archs_s)s; do \
    (cd $arch/ && (for f in ../%(primar_arch)s/%(noarch_rpms)s; do \
        ln -sf $f ./; done)); done
"""


def mk_cmds_to_deploy_rpms(repo, srpm, noarch=None, bdist=None):
    """
    Make up list of command strings to build given srpm.

    :param repo: Repo instance
    :param srpm: srpm path
    :param noarch: True or False if built RPM is noarch/arch-dependent
    :param bdist: Build dist (name-version), e.g. 'fedora-custom-19'

    :return: List of commands to build given srpm
    """
    assert isinstance(repo, MR.Repo), "Wrong arg repo of type " + repr(repo)

    if noarch is None:
        noarch = RU.is_noarch(srpm)

    if bdist is None:
        bdist = repo.dist

    dcmd = repo.server.deploy_cmd
    c0 = dcmd(os.path.join(rpmdir, "*.src.rpm"),
              os.path.join(repo.destdir, "sources"))

    if noarch:
        rpmdir = "/var/lib/mock/%s-%s/result/" % (bdist, repo.primary_arch)

        ctx = dict(other_archs_s=' '.join(repo.other_archs),
                   primar_arch=repo.primar_arch,
                   noarch_rpms="*.noarch.rpm")
        (sc, sc_dir) = repo.adjust_cmd(_MK_SYMLINKS_TO_NOARCH_RPM % ctx)

        bc = SH.bind(dcmd(os.path.join(rpmdir, "*.noarch.rpm"),
                          os.path.join(repo.destdir, repo.primary_arch)), sc)
        cs = [c0, bc]
    else:
        cs = [c0] + [dcmd(os.path.join(rpmdir, "*.%s.rpm" % a),
                          os.path.join(repo.destdir, a)) for a in repo.archs]

    return cs


# vim:sw=4:ts=4:et:
