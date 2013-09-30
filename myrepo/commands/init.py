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
from myrepo.commands.utils import assert_repo, assert_ctx_has_key, \
    setup_workdir

import myrepo.commands.genconf as MCG
import myrepo.shell as MS
import myrepo.utils as MU
import glob
import logging
import os.path


def _join_dirs(prefix, dirs):
    """
    >>> _join_dirs("/tmp", ["abc", "def"])
    '/tmp/{abc,def}'
    """
    return os.path.join(prefix, "{%s}" % ','.join(dirs))


def prepare_0(repo):
    """
    Make up list of command strings to initialize repo.

    :param repo: myrepo.repo.Repo instance
    :return: List of command strings to deploy built RPMs.
    """
    assert_repo(repo)

    dirs_s = _join_dirs(repo.destdir, repo.archs + ["sources"])
    return [repo.mk_cmd("mkdir -p " + dirs_s)[0]]


def prepare(repos):
    """
    Make up list of command strings to update metadata of given repos.
    It's similar to above ``prepare_0`` but applicable to multiple repos.

    :param repos: List of Repo instances

    :return: List of command strings to deploy built RPMs.
    """
    return MU.concat(prepare_0(repo) for repo in repos)


def run(ctx):
    """
    Initialize yum repos.

    :param ctx: Application context
    :return: True if commands run successfully else False
    """
    assert_ctx_has_key(ctx, "repos")

    cs = prepare(ctx["repos"])

    if ctx.get("dryrun", False):
        for c in cs:
            print c

        if ctx.get("genconf", False):
            return MCG.run(ctx)

        return True

    logging.info("Run myrepo.commands.init.run...")
    if all(MS.prun(cs, dict(logfile=False, ))):
        return MCG.run(ctx) if ctx.get("genconf", False) else True
    else:
        RuntimeError("Could not initialize the yum repos")


# vim:sw=4:ts=4:et:
