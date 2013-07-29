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
import myrepo.repoops as RO
import myrepo.utils as U
import rpmkit.rpmutils as RU
import rpmkit.shell2 as SH   # make use of gevent-powered version.

from myrepo.hooks import hook

import glob
import logging
import os
import os.path
import subprocess
import tempfile


# Aliases
is_noarch = RU.is_noarch


def __setup_workdir(prefix, topdir="/tmp"):
    return tempfile.mkdtemp(dir=topdir, prefix=prefix)


@hook
def init(ctx):
    """
    Initialize yum repository.

    :param ctx: Application context object holding parameters
    :return: True if success else False
    """
    repo = ctx.repo
    rc = SH.run("mkdir -p " + " ".join(repo.rpmdirs()), repo.user, repo.server,
                timeout=repo.timeout)

    if rc and ctx.genconf:
        rc = genconf(ctx)

    return rc


@hook
def genconf(ctx):
    """
    Generate repo configuration files (release file and mock.cfg) and RPMs.

    :param ctx: Application context object holding parameters
    :return: True if success else False
    """
    workdir = __setup_workdir("myrepo_" + repo.name + "-release-")

    repo = ctx.repo
    srpms = [RO.build_release_srpm(repo, workdir),
             RO.build_mock_cfg_srpm(repo, workdir)]

    assert len(srpms) == 2, "Failed to make release and/or mock.cfg SRPMs"

    for srpm in srpms:
        deploy(ctx)

    return 0


@hook
def update(ctx):
    """
    Update and synchronize repository's metadata, that is, run
    'createrepo --update ...', etc.

    :param ctx: Application context object holding parameters
    :return: True if success else False
    """
    repo = ctx.repo
    destdir = repo.destdir()

    # hack: degenerate noarch rpms
    if repo.multiarch:
        c = "for d in %s; do (cd $d && ln -sf ../%s/*.noarch.rpm ./); done"
        c = c % (" ".join(repo.archs[1:]), repo.primary_arch)

        SH.run(c, repo.user, repo.server, repo.destdir(), repo.timeout,
               stop_on_error=True)  # RuntimeError will be thrown if failed.

    c = "test -d repodata"
    c += " && createrepo --update --deltas --oldpackagedirs . --database ."
    c += " || createrepo --deltas --oldpackagedirs . --database ."

    largs = [([c, repo.user, repo.server, d, repo.timeout],
              dict(stop_on_error=True)) for d in repo.rpmdirs()]
    return SH.prun(largs)


def _build(repo, srpm):
    """
    Build given SRPM file.

    :param repo: myrepo.repo.Repo object
    :param srpm: Path to src.rpm to build

    :return: True if success else False
    """
    largs = [([d.build_cmd(srpm), ], dict(timeout=repo.timeout)) for d in
             dists_by_srpm(repo, srpm)]

    return SH.prun(largs)


def __dists_by_srpm(repo, srpm):
    """
    :param repo: myrepo.repo.Repo object
    :param srpm: Path to src.rpm to build

    :return: List of myrepo.distribution.Distribution objects
    """
    return repo.dists[:1] if is_noarch(srpm) else repo.dists


@hook
def build_srpm(repo, srpm):
    """
    Build src.rpm and make up a list of RPMs to deploy and sign.

    FIXME: ugly code around signkey check.

    :param repo: myrepo.repo.Repo object
    :param srpm: Path to src.rpm to build
    """
    assert all(_build(repo, srpm))

    destdir = repo.destdir()
    rpms_to_deploy = []  # :: [(rpm_path, destdir)]
    rpms_to_sign = []

    for d in __dists_by_srpm(repo, srpm):
        rpmdir = d.rpmdir()

        srpms_to_copy = glob.glob(os.path.join(rpmdir, "*.src.rpm"))
        assert srpms_to_copy, "Could not find src.rpm in " + rpmdir

        srpm_to_copy = srpms_to_copy[0]
        rpms_to_deploy.append((srpm_to_copy, os.path.join(destdir, "sources")))

        brpms = [f for f in glob.glob(rpmdir + "/*.rpm")
                 if not f.endswith(".src.rpm")]
        logging.debug("rpms=" + str([os.path.basename(f) for f in brpms]))

        for p in brpms:
            rpms_to_deploy.append((p, os.path.join(destdir, d.arch)))

        rpms_to_sign += brpms

    # Dirty hack:
    setattr(repo, "rpms_to_deploy", rpms_to_deploy)
    setattr(repo, "rpms_to_sign", rpms_to_sign)

    return True


@hook
def build(ctx):
    """
    Build src.rpm and make up a list of RPMs to deploy and sign.

    FIXME: ugly code around signkey check.

    :param ctx: Application context object holding parameters
    """
    assert ctx.srpms, "'build' command requires arguments of srpm paths"

    return all(build_srpm(ctx.repo, srpm) for srpm in ctx.srpms)


def _deploy_cmd(repo, src, dst):
    """
    Make up and and return command strings to deploy RPMs from ``src`` to
    ``dst`` for the yum repository ``repo``.

    :param repo: myrepo.repo.Repo object
    :return: Deploying command string :: str
    """
    if U.is_local(repo.server):
        if "~" in dst:
            dst = os.path.expanduser(dst)

        return "cp -a %s %s" % (src, dst)
    else:
        return "scp -p %s %s@%s:%s" % (src, repo.user, repo.server, dst)


def _deploy(repo, *args, **kwargs):
    """
    Deploy built RPMs.

    :param repo: myrepo.repo.Repo object
    :return: True if success else False
    """
    largs = [(_deploy_cmd(repo, rpm, dest), dict(timeout=repo.timeout))
             for rpm, dest in repo.rpms_to_deploy]

    rcs = SH.prun(largs)
    assert all(rcs), "results=" + str(rcs)

    rcs = update(repo)
    assert all(rcs), "results=" + str(rcs)

    return True


@hook
def deploy(ctx):
    """
    Build and deploy RPMs.

    :param ctx: Application context object holding parameters
    :return: True if success else False
    """
    results = [(srpm, build_srpm(ctx.repo, srpm) and _deploy(ctx.repo)) for
               srpm in ctx.srpms]

    ret = True
    for srpm, rc in results:
        if rc:
            logging.info("Success: " + srpm)
        else:
            logging.warn("Fail: " + srpm)
            ret = False

    return ret


# vim:sw=4:ts=4:et:
