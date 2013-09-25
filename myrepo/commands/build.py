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
import myrepo.commands.utils as MAU

import myrepo.shell as MS
import myrepo.utils as MU

import itertools
import logging
import os.path


def _log_opt(level=logging.getLogger().level):
    """
    Compute logging option string append to the tail of the command string
    later, to tune command execution verbosity level.

    >>> _log_opt(logging.INFO)
    ''
    >>> _log_opt(logging.WARN)
    ' > /dev/null 2> /dev/null'
    >>> _log_opt(logging.DEBUG)
    ' -v'

   :param level: Logging level
    """
    if level >= logging.WARN:
        return " > /dev/null 2> /dev/null"
    else:
        return " -v" if level < logging.INFO else ''


def prepare_0(repo, srpm, level=logging.getLogger().level):
    """
    Make up list of command strings to deploy built RPMs.

    :param repo: myrepo.repo.Repo instance
    :param srpm: myrepo.srpm.Srpm instance
    :param level: Logging level

    :return: List of command strings to deploy built RPMs.
    """
    MAU.assert_repo(repo)
    MAU.assert_srpm(srpm)

    f = lambda b: "mock -r %s %s%s" % (b, srpm.path, _log_opt(level))

    return [f(b) for b in repo.list_build_labels(srpm)]


def prepare(repos, srpm, level=logging.getLogger().level):
    """
    Make up list of command strings to update metadata of given repos.
    It's similar to above ``prepare_0`` but applicable to multiple repos.

    :param repos: List of Repo instances
    :param srpm: myrepo.srpm.Srpm instance

    :return: List of command strings to deploy built RPMs.
    """
    return MU.concat(prepare_0(repo, srpm, level) for repo in repos)


def run(ctx):
    """
    :param ctx: Application context

    :return: True if commands run successfully else False
    """
    assert "repos" in ctx, "No repos defined in given ctx!"
    assert "srpm" in ctx, "No srpm defined in given ctx!"

    cs = prepare(ctx["repos"], ctx["srpm"])

    if ctx.get("dryrun", False):
        for c in cs:
            print c

        return True

    ps = [MS.run_async(c, logfile=False) for c in cs]
    return all(MS.stop_async_run(p) for p in ps)


# vim:sw=4:ts=4:et:
