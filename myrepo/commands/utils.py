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
import myrepo.srpm as MS

import logging
import os.path
import os
import sys
import tempfile


_TMPDIR = os.environ.get("TMPDIR", "/tmp")


def assert_repo(repo):
    assert isinstance(repo, MR.Repo), "Wrong arg repo of type " + repr(repo)


def assert_srpm(srpm):
    assert isinstance(srpm, MS.Srpm), "Wrong arg srpm of type " + repr(srpm)


def setup_workdir(prefix="myrepo-workdir-", topdir=_TMPDIR):
    """
    Create temporal working dir to put data and log files.
    """
    return tempfile.mkdtemp(dir=topdir, prefix=prefix)


def init_workdir(workdir):
    """
    Initialize (create) working dir if not exists and return its path.

    FIXME: This is a quick and dirty hack.

    :param workdir: Working dir path or None
    :return: The path to working dir (created)
    """
    m = "Created workdir %s. This dir will be kept as it is. " + \
        "Please remove it manually if you do not want to keep it."

    if workdir:
        # Return immediately to avoid to log more than twice if dir exists.
        if os.path.exists(workdir):
            return workdir

        os.makedirs(workdir)
    else:
        workdir = setup_workdir()

    logging.info(m % workdir)
    return workdir


def print_commands_and_exit_if_dryrun(ctx, cs):
    """
    :param ctx: Application context object holding parameters
    :param cs: List of command strings to run
    """
    if "dryrun" in ctx:
        "commands to run:"
        for c in cs:
            print "# " + c

        sys.exit(0)


# vim:sw=4:ts=4:et:
