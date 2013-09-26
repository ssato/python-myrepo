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
import myrepo.commands.utils as MCU
import myrepo.shell as MS
import myrepo.utils as MU
import os.path


_CMD_TEMPLATE = """\
test -d repodata \
&& createrepo --update --deltas --oldpackagedirs . --database . \
|| createrepo --deltas --oldpackagedirs . --database ."""


def prepare_0(repo, ctmpl=_CMD_TEMPLATE):
    """
    Make up a list of command strings to update metadata of given repo.

    :param repo: Repo instance
    :param ctmpl: Command string template

    :return: List of commands to update metadata of ``repo``
    """
    MCU.assert_repo(repo)

    return [c for c, _d in (repo.mk_cmd(ctmpl, os.path.join(repo.destdir, a))
            for a in ["sources"] + repo.archs)]


def prepare(repos, ctmpl=_CMD_TEMPLATE):
    """
    Make up a list of command strings to update metadata of given repos. It's
    similar to above ``prepare_0`` but will be applied to multiple repos.

    :param repos: List of Repo instances
    :param ctmpl: Command string template

    :return: List of commands to update metadata of ``repos``
    """
    return MU.concat(prepare_0(repo, ctmpl) for repo in repos)


def run(ctx, ctmpl=_CMD_TEMPLATE):
    """
    :param repos: List of Repo instances

    :return: True if commands run successfully else False
    """
    MCU.assert_ctx_has_key(ctx, "repos")

    cs = prepare(ctx["repos"])

    if ctx.get("dryrun", False):
        for c in cs:
            print c

        return True

    return all(MS.prun(cs, dict(logfile=False, )))


# vim:sw=4:ts=4:et:
