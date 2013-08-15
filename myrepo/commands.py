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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from myrepo.hooks import hook

import myrepo.shell as SH  # Use local copy instead of rpmkit.shell2
import myrepo.utils as U
import rpmkit.rpmutils as RU

import datetime
import glob
import locale
import logging
import os
import os.path
import subprocess
import tempfile
import time


_SIGN = "rpm --resign --define '_signature gpg' --define '_gpg_name %s' %s"

_TMPDIR = os.environ.get("TMPDIR", "/tmp")

# Aliases
is_noarch = RU.is_noarch


def __setup_workdir(prefix="myrepo-workdir-", topdir=_TMPDIR):
    """
    Create temporal working dir to put data and log files.
    """
    return tempfile.mkdtemp(dir=topdir, prefix=prefix)


def _init_workdir(workdir):
    """
    Initialize (create) working dir if not exists and return its path.

    FIXME: This is a quick and dirty hack.

    :param workdir: Working dir path or None
    :return: The path to working dir (created)
    """
    m = "Created workdir %s. This dir will be kept as it is. " + \
        "Please remove it manually if you do not want to keep it."

    if workdir:
        if os.path.exists(workdir):
            return None  # Avoid to log more than twice.

        os.makedirs(workdir)
    else:
        workdir = __setup_workdir()

    logging.info(m % workdir)
    return workdir


def sign_rpms_cmd(keyid=None, rpms=[], ask=True, fmt=_SIGN):
    """
    Make up the command string to sign RPMs.

    >>> exp = "rpm --resign --define '_signature gpg' "
    >>> exp += "--define '_gpg_name ABCD123' a.rpm b.rpm"
    >>> exp == sign_rpms_cmd("ABCD123", ["a.rpm", "b.rpm"])
    True

    TODO: It might ask user about the gpg passphrase everytime this method is
    called.  How to store the passphrase or streamline that with gpg-agent ?

    :param keyid: GPG Key ID to sign with :: str
    :param rpms: RPM file path list :: [str]
    :param ask: Ask key ID if both ``keyid`` and this are None
    """
    if keyid is None and ask:
        keyid = raw_input("Input GPG Key ID to sign RPMs > ").strip()

    return fmt % (keyid, ' '.join(rpms))


def _deploy(ctx):
    """
    Deploy built RPMs.

    SEE ALSO: :function:``build_srpm``

    TODO: Set build timeout.

    :param ctx: Application context object holding parameters
    :return: True if success else AssertionError will be raised.
    """
    workdir = _init_workdir(ctx.get("workdir", None))
    if workdir:
        ctx["workdir"] = workdir

    def logfile(rpm):
        return os.path.join(ctx["workdir"],
                            "deploy.%s.log" % os.path.basename(rpm))

    repo = ctx["repo"]
    largs = [([_deploy_cmd(repo, rpm, dest), ],
              dict(timeout=None, logfile=logfile(rpm)))
             for rpm, dest in ctx.get("rpms_to_deploy", [])]

    rcs = SH.prun(largs)
    rpms = ', '.join(rpm for rpm, _dest in ctx.get("rpms_to_deploy", []))
    assert all(rcs), "Failed to deply: rpms=%s" % rpms

    rcs = update(ctx)
    assert all(rcs), "Failed to update the repo metadata."

    return True


# Commands:
@hook
def init(ctx):
    """
    Initialize yum repository.

    :param ctx: Application context object holding parameters
    :return: True if success else False
    """
    workdir = _init_workdir(ctx.get("workdir", None))
    if workdir:
        ctx["workdir"] = workdir

    logfile = os.path.join(ctx["workdir"], "init.log")

    repo = ctx["repo"]
    rc = SH.run("mkdir -p " + ' '.join(repo.rpmdirs), repo.server_user,
                repo.server_name, logfile=logfile, timeout=None,
                conn_timeout=repo.server_timeout)

    if rc and ctx.get("genconf", False):
        rc = genconf(ctx)

    return rc


@hook
def genconf(ctx):
    """
    Generate repo configuration files (release file and mock.cfg) and RPMs.

    :param ctx: Application context object holding parameters
    :return: True if success else False
    """
    workdir = _init_workdir(ctx.get("workdir", None))
    if workdir:
        ctx["workdir"] = workdir

    repo = ctx["repo"]
    srpm = build_repodata_srpm(ctx, ctx["workdir"], ctx["tpaths"],
                               os.path.join(ctx["workdir"], "genconf.log"))

    if srpm is None:
        logging.error("Failed to build yum repo release SRPM. "
                      "Check to see files in " + workdir)
        return 1

    ctx["srpms"] = [srpm]
    return deploy(ctx)


@hook
def update(ctx):
    """
    Update and synchronize repository's metadata, that is, run
    'createrepo --update ...', etc.

    :param ctx: Application context object holding parameters
    :return: True if success else False
    """
    workdir = _init_workdir(ctx.get("workdir", None))
    if workdir:
        ctx["workdir"] = workdir

    repo = ctx["repo"]
    cf = "for d in %s; " + \
         "do (cd $d && (for f in ../%s/*.noarch.rpm; " + \
         "do test -f $f && ln -sf $f ./ || :; done)); done"

    # hack: degenerate noarch rpms
    if repo.multiarch:
        c = cf % (" ".join(repo.archs[1:]), repo.primary_arch)

        SH.run(c, repo.server_user, repo.server_name, repo.destdir,
               logfile=os.path.join(ctx["workdir"], "update.0.log"),
               timeout=None, conn_timeout=repo.server_timeout,
               stop_on_error=True)

    c = "test -d repodata"
    c += " && createrepo --update --deltas --oldpackagedirs . --database ."
    c += " || createrepo --deltas --oldpackagedirs . --database ."

    largs = [([c, repo.server_user, repo.server_name, d],
              dict(logfile=os.path.join(d, "update.1.log"), timeout=None,
                   conn_timeout=repo.server_timeout, stop_on_error=True))
             for d in repo.rpmdirs]

    return SH.prun(largs)


@hook
def build(ctx):
    """
    Build src.rpm and make up a list of RPMs to deploy and sign.

    FIXME: ugly code around signkey check.

    :param ctx: Application context object holding parameters
    """
    assert "srpms" in ctx, "'build' command requires arguments of srpm paths"

    workdir = _init_workdir(ctx.get("workdir", None))
    if workdir:
        ctx["workdir"] = workdir

    rc = True
    for srpm in ctx["srpms"]:
        logfile = os.path.join(workdir,
                               "build.%s.log" % os.path.basename(srpm))
        if not _build_srpm(ctx, srpm, logfile):
            rc = False

    return rc


@hook
def deploy(ctx):
    """
    Build and deploy RPMs.

    :param ctx: Application context object holding parameters
    :return: True if success else False
    """
    results = [(srpm, _build_srpm(ctx, srpm) and _deploy(ctx)) for
               srpm in ctx["srpms"]]

    ret = True
    for srpm, rc in results:
        if rc:
            logging.debug("Success: " + srpm)
        else:
            logging.warn("Fail: " + srpm)
            ret = False

    return ret


# vim:sw=4:ts=4:et:
