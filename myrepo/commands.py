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
import rpmkit.shell as SH

from myrepo.hooks import hook

import glob
import logging
import os
import os.path
import subprocess
import tempfile


def __setup_workdir(prefix, topdir="/tmp"):
    return tempfile.mkdtemp(dir=topdir, prefix=prefix)


@hook
def init(repo, *args, **kwargs):
    """Initialize yum repository.

    :param repo: myrepo.repo.Repo object
    """
    rc = SH.run(
        "mkdir -p " + " ".join(repo.rpmdirs()), repo.user, repo.server,
        timeout=repo.timeout,
    )

    if repo.genconf and rc == 0:
        rc = genconf(repo)

    return rc


@hook
def genconf(repo, *args, **kwargs):
    workdir = __setup_workdir("myrepo_" + repo.name + "-release-")

    srpms = [
        RO.build_release_srpm(repo, workdir),
        RO.build_mock_cfg_srpm(repo, workdir)
    ]

    assert len(srpms) == 2, "Failed to make release and/or mock.cfg SRPMs"

    for srpm in srpms:
        deploy(repo, srpm, True)

    return 0


@hook
def update(repo, *args, **kwargs):
    """Update and synchronize repository's metadata.

    :param repo: myrepo.repo.Repo object
    """
    return repo.update_metadata()


@hook
def build(repo, srpm, *args, **kwargs):
    """
    FIXME: ugly code around signkey check.

    :param repo: myrepo.repo.Repo object
    :param srpm: Path to src.rpm to build
    """
    assert all(rc == 0 for rc in RO.build(repo, srpm))

    destdir = repo.destdir()
    rpms_to_deploy = []  # :: [(rpm_path, destdir)]
    rpms_to_sign = []

    for d in RO.dists_by_srpm(repo, srpm):
        rpmdir = d.rpmdir()

        srpms_to_copy = glob.glob(rpmdir + "/*.src.rpm")
        assert srpms_to_copy, "Could not find src.rpm in " + rpmdir

        srpm_to_copy = srpms_to_copy[0]
        rpms_to_deploy.append((srpm_to_copy, os.path.join(destdir, "sources")))

        brpms = [
            f for f in glob.glob(rpmdir + "/*.rpm") \
                if not f.endswith(".src.rpm")
        ]
        logging.debug("rpms=" + str([os.path.basename(f) for f in brpms]))

        for p in brpms:
            rpms_to_deploy.append((p, os.path.join(destdir, d.arch)))

        rpms_to_sign += brpms

    # Dirty hack:
    setattr(repo, "rpms_to_deploy", rpms_to_deploy)
    setattr(repo, "rpms_to_sign", rpms_to_sign)

    return 0


@hook
def deploy_rpms(repo, *args, **kwargs):
    tasks = [
        SH.Task(
            RO.copy_cmd(repo, rpm, dest), timeout=repo.timeout
        ) for rpm, dest in repo.rpms_to_deploy
    ]
    rcs = SH.prun(tasks)
    assert all(rc == 0 for rc in rcs), "results=" + str(rcs)

    rcs = update(repo)
    assert all(rc == 0 for rc in rcs), "results=" + str(rcs)

    return 0


@hook
def deploy(repo, srpm, *args, **kwargs):
    return deploy_rpms(repo) if build(repo, srpm) == 0 else 1


# vim:sw=4:ts=4:et:
