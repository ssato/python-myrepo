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


def _datestamp(d=datetime.datetime.now()):
    """
    Make up a date string to be used in %changelog section of RPM SPEC files.

    >>> _datestamp(datetime.datetime(2013, 7, 31))
    'Wed Jul 31 2013'
    """
    locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
    return datetime.datetime.strftime(d, "%a %b %e %Y")


def __setup_workdir(prefix="myrepo-workdir-", topdir=_TMPDIR):
    """
    Create temporal working dir to put data and log files.
    """
    return tempfile.mkdtemp(dir=topdir, prefix=prefix)


def build_repodata_srpm(ctx, workdir, tpaths, logfile=None):
    """
    Generate .repo file, mock.cfg files and rpm spec for the repo
    (ctx["repo"]), build src.rpm contains them, and returns the path of
    built src.rpm.

    :param ctx: Application context object
    :param workdir: Working dir to build RPMs
    :param tpaths: Template path list :: [str]
    """
    assert os.path.realpath(workdir) != os.path.realpath(os.curdir), \
        "Workdir must not be curdir!"

    repo = ctx["repo"]

    repofile = gen_repo_file(repo, workdir, tpaths)
    rpmspec = gen_rpmspec(ctx, workdir, tpaths)

    for d in repo.dists:  # d :: myrepo.distributed.Dist
        mpath = os.path.join(workdir, "%s-%s.cfg" % (repo.dist, d.arch))
        open(mpath, 'w').write(gen_mock_cfg_content(repo, d, tpaths))

    if logfile is None:
        logfile = os.path.join(workdir, "build_repodata_srpm.log")

    vopt = " --verbose" if logging.getLogger().level < logging.INFO else ''

    c = "rpmbuild --define '_srcrpmdir .' --define '_sourcedir .' " + \
        "--define '_buildroot .' -bs %s%s" % (os.path.basename(rpmspec), vopt)

    if SH.run(c, workdir=workdir, logfile=logfile):
        srpms = glob.glob(os.path.join(workdir, "*.src.rpm"))
        assert srpms, "No src.rpm found in " + workdir

        return srpms[0] if srpms else None
    else:
        logging.warn("Failed to build yum repodata RPM from " + rpmspec)
        return None


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


def _dists_by_srpm(repo, srpm):
    """
    :param repo: myrepo.repo.Repo object
    :param srpm: Path to src.rpm to build

    :return: List of myrepo.distribution.Dist objects to build given srpm
    """
    return repo.dists[:1] if is_noarch(srpm) else repo.dists


def _build(repo, srpm, logfile=False):
    """
    Build given SRPM file.

    TODO: Set build timeout.

    :param repo: myrepo.repo.Repo object
    :param srpm: Path to src.rpm to build

    :return: True if success else False
    """
    rc = True

    for d in _dists_by_srpm(repo, srpm):
        c = d.build_cmd(srpm)
        logging.info("Build srpm: " + srpm)

        if not SH.run(c, timeout=None, logfile=logfile):
            rc = False

    return rc


def _build_srpm(ctx, srpm, logfile=False):
    """
    Build src.rpm and make up a list of RPMs to deploy and sign.

    FIXME: Ugly code around signkey check and setting RPMs to deploy.

    :param ctx: Application context object :: dict
    :param srpm: Path to src.rpm to build
    """
    repo = ctx["repo"]

    if not _build(repo, srpm, logfile):
        raise RuntimeError("Failed to build: " + srpm)

    destdir = repo.destdir
    rpms_to_deploy = []  # :: [(rpm_path, destdir)]
    rpms_to_sign = []

    for d in _dists_by_srpm(repo, srpm):
        rpmdir = d.rpmdir()

        srpms_to_copy = glob.glob(os.path.join(rpmdir, "*.src.rpm"))
        assert srpms_to_copy, "Could not find src.rpm in " + rpmdir

        srpm_to_copy = srpms_to_copy[0]
        rpms_to_deploy.append((srpm_to_copy, os.path.join(destdir, "sources")))

        brpms = [f for f in glob.glob(os.path.join(rpmdir, "*.rpm"))
                 if not f.endswith(".src.rpm")]

        m = "Found rpms: " + str([os.path.basename(f) for f in brpms])
        logging.debug(m)

        for p in brpms:
            rpms_to_deploy.append((p, os.path.join(destdir, d.arch)))

        rpms_to_sign += brpms

    # Save these to deploy later.
    ctx["rpms_to_deploy"] = rpms_to_deploy
    ctx["rpms_to_sign"] = rpms_to_sign

    return True


def _deploy_cmd(repo, src, dst):
    """
    Make up and and return command strings to deploy RPMs from ``src`` to
    ``dst`` for the yum repository ``repo``.

    :param repo: myrepo.repo.Repo object
    :return: Deploying command string :: str
    """
    if repo.server_is_local:
        if "~" in dst:
            dst = os.path.expanduser(dst)

        return "cp -a %s %s" % (src, dst)
    else:
        return "scp -p %s %s@%s:%s" % (src, repo.server_user,
                                       repo.server_name, dst)


def _deploy(ctx):
    """
    Deploy built RPMs.

    SEE ALSO: :function:``build_srpm``

    TODO: Set build timeout.

    :param ctx: Application context object holding parameters
    :return: True if success else AssertionError will be raised.
    """
    workdir = _init_workdir(ctx)
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


def _init_workdir(ctx):
    """
    Initialize working dir.

    FIXME: This is a quick and dirty hack.
    """
    m = "Created workdir %s. This dir will be kept as it is. " + \
        "Please remove it manually if you do not want to keep it."
    workdir = ctx.get("workdir", False)
    ret = None

    if workdir:
        if os.path.exists(workdir):
            return ret  # Avoid to output the notification message.

        os.makedirs(workdir)
    else:
        workdir = ret = __setup_workdir()

    logging.info(m % workdir)
    return ret


# Commands:
@hook
def init(ctx):
    """
    Initialize yum repository.

    :param ctx: Application context object holding parameters
    :return: True if success else False
    """
    workdir = _init_workdir(ctx)
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
    workdir = _init_workdir(ctx)
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
    workdir = _init_workdir(ctx)
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

    workdir = _init_workdir(ctx)
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
