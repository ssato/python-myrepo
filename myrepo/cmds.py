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


def mk_cmds_to_deploy_rpms(repo, bdist=None):
    """
    Make up list of command strings to build given srpm.

    :param repo: Repo instance
    :param bdist: Build dist (name-version), e.g. 'fedora-custom-19'

    :return: List of commands to build given srpm
    """
    assert isinstance(repo, MR.Repo), "Wrong arg repo of type " + repr(repo)

    if bdist is None:
        bdist = repo.dist

    pass

# vim:sw=4:ts=4:et:
