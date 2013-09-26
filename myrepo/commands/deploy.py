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
import myrepo.commands.build as MCB
import myrepo.commands.utils as MCU

import myrepo.shell as MS
import myrepo.utils as MU

import itertools
import os.path


_MK_SYMLINKS_TO_NOARCH_RPM = """\
for arch in %(other_archs_s)s; do \
(cd $arch/ && (for f in ../%(primary_arch)s/%(noarch_rpms)s; do \
ln -sf $f ./; done)); done"""


def prepare_0(repo, srpm, build=False):
    """
    Make up list of command strings to deploy built RPMs.

    :param repo: myrepo.repo.Repo instance
    :param srpm: myrepo.srpm.Srpm instance
    :param build: Build given srpm before deployment

    :return: List of command strings to deploy built RPMs.
    """
    MCU.assert_repo(repo)
    MCU.assert_srpm(srpm)

    if build:
        bcs = MCB.prepare_0(repo, srpm)

    dcmd = repo.server.deploy_cmd
    rpmdirs = repo.mockdirs(srpm)
    rpmname_pre = "%s-%s-" % (srpm.name, srpm.version)
    c0 = dcmd(os.path.join(rpmdirs[0], rpmname_pre + "*.src.rpm"),
              os.path.join(repo.destdir, "sources"))

    if srpm.noarch:
        noarch_rpms = rpmname_pre + "*.noarch.rpm"

        if repo.other_archs:
            ctx = dict(other_archs_s=' '.join(repo.other_archs),
                       primary_arch=repo.primary_arch,
                       noarch_rpms=noarch_rpms)
            (sc, sc_dir) = repo.adjust_cmd(_MK_SYMLINKS_TO_NOARCH_RPM % ctx,
                                           repo.destdir)

            bc = MS.bind(dcmd(os.path.join(rpmdirs[0], noarch_rpms),
                              os.path.join(repo.destdir, repo.primary_arch)),
                         sc)[0]
        else:
            bc = dcmd(os.path.join(rpmdirs[0], noarch_rpms),
                      os.path.join(repo.destdir, repo.primary_arch))

        cs = [" && ".join([bcs[0], c0, bc])] if build else [c0, bc]
    else:
        cs = [dcmd(os.path.join(d, rpmname_pre + "*.%s.rpm" % a),
              os.path.join(repo.destdir, a)) for d, a
              in itertools.izip(rpmdirs, repo.archs)]

        if build:
            cs = [MS.bind(bc, c)[0] for bc, c in itertools.izip(bcs, cs)]
            cs[0] = MS.bind(cs[0], c0)[0]
        else:
            cs = [c0] + cs

    return cs


def prepare(repos, srpm, build=False):
    """
    Make up list of command strings to update metadata of given repos.
    It's similar to above ``prepare_0`` but applicable to multiple repos.

    :param repos: List of Repo instances
    :param srpm: myrepo.srpm.Srpm instance
    :param build: Build given srpm before deployment

    :return: List of command strings to deploy built RPMs.
    """
    return MU.concat(prepare_0(repo, srpm, build) for repo in repos)


def run(ctx):
    """
    :param ctx: Application context
    :return: True if commands run successfully else False
    """
    assert "repos" in ctx, "No repos defined in given ctx!"
    assert "srpm" in ctx, "No srpm defined in given ctx!"

    cs = [c for c in prepare(ctx["repos"], ctx["srpm"],
                             ctx.get("build", False))]

    return all(MS.prun(cs, dict(logfile=False, )))


# vim:sw=4:ts=4:et:
