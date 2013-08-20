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
from myrepo.hooks import hook

import myrepo.repo as MR
import myrepo.shell as SH
import myrepo.utils as U
import rpmkit.rpmutils as RU

import logging
import os.path
import os
import tempfile


_TMPDIR = os.environ.get("TMPDIR", "/tmp")


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


def _build_cmd(label, srpm):
    """
    Make up a command string to build given ``srpm``.

    NOTE: mock will print log messages to stderr (not stdout).

    >>> logging.getLogger().setLevel(logging.INFO)
    >>> _build_cmd("fedora-19-x86_64", "/tmp/abc-0.1.src.rpm")
    'mock -r fedora-19-x86_64 /tmp/abc-0.1.src.rpm'

    >>> logging.getLogger().setLevel(logging.WARN)
    >>> _build_cmd("fedora-19-x86_64", "/tmp/abc-0.1.src.rpm")
    'mock -r fedora-19-x86_64 /tmp/abc-0.1.src.rpm > /dev/null 2> /dev/null'

    >>> logging.getLogger().setLevel(logging.DEBUG)
    >>> _build_cmd("fedora-19-x86_64", "/tmp/abc-0.1.src.rpm")
    'mock -r fedora-19-x86_64 /tmp/abc-0.1.src.rpm -v'

    :param label: Label of build target distribution,
        e.g. fedora-19-x86_64, fedora-custom-19-x86_64
    :param srpm: SRPM path to build

    :return: A command string to build given ``srpm``
    """
    # suppress log messages from mock by log level:
    level = logging.getLogger().level
    if level >= logging.WARN:
        log = " > /dev/null 2> /dev/null"
    else:
        log = " -v" if level < logging.INFO else ""

    return "mock -r %s %s%s" % (label, srpm, log)


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
        return [_build_cmd(label, srpm)]
    else:
        return [_build_cmd("%s-%s" % (bdist, a), srpm) for a in repo.archs]


_MK_SYMLINKS_TO_NOARCH_RPM = """\
for arch in %(other_archs_s)s; do \
(cd $arch/ && (for f in ../%(primary_arch)s/%(noarch_rpms)s; do \
ln -sf $f ./; done)); done"""


def mk_cmds_to_deploy_rpms(repo, srpm, noarch=None, bdist=None):
    """
    Make up list of command strings to build given srpm.

    :param repo: Repo instance
    :param srpm: srpm path
    :param noarch: True or False if built RPM is noarch/arch-dependent
    :param bdist: Build dist (name-version), e.g. 'fedora-custom-19'

    :return: List of commands to build given srpm
    """
    assert isinstance(repo, MR.Repo), "Wrong arg repo of type " + repr(repo)

    if noarch is None:
        noarch = RU.is_noarch(srpm)

    if bdist is None:
        bdist = repo.dist

    dcmd = repo.server.deploy_cmd
    rpmdir = "/var/lib/mock/%s-%%s/result" % bdist
    c0 = dcmd(os.path.join(rpmdir % repo.primary_arch, "*.src.rpm"),
              os.path.join(repo.destdir, "sources"))

    if noarch:
        rpmdir = rpmdir % repo.primary_arch
        ctx = dict(other_archs_s=' '.join(repo.other_archs),
                   primary_arch=repo.primary_arch,
                   noarch_rpms="*.noarch.rpm")
        (sc, sc_dir) = repo.adjust_cmd(_MK_SYMLINKS_TO_NOARCH_RPM % ctx,
                                       repo.destdir)

        bc = SH.bind(dcmd(os.path.join(rpmdir, "*.noarch.rpm"),
                          os.path.join(repo.destdir, repo.primary_arch)),
                     sc)[0]
        cs = [c0, bc]
    else:
        cs = [c0] + [dcmd(os.path.join(rpmdir % a, "*.%s.rpm" % a),
                          os.path.join(repo.destdir, a)) for a in repo.archs]

    return cs


_UPDATE_REPO_METADATA = """\
test -d repodata \
&& createrepo --update --deltas --oldpackagedirs . --database . \
|| createrepo --deltas --oldpackagedirs . --database ."""


def mk_cmds_to_update(repo, *args, **kwargs):
    """
    Make up list of command strings to update repo metadata.

    :param repo: Repo instance
    :return: List of commands to update repo metadata
    """
    return [c for c, _d in
            (repo.adjust_cmd(_UPDATE_REPO_METADATA,
                             os.path.join(repo.destdir, a)) for a in
             repo.archs)]


def mk_cmds_to_init__no_genconf(repo, *args, **kwargs):
    """
    Make up list of command strings to update repo metadata.

    :param repo: Repo instance
    :return: List of commands to update repo metadata
    """
    dirs_s = os.path.join(repo.destdir,
                          "{%s}" % ','.join(repo.archs + ["sources"]))
    return [repo.adjust_cmd("mkdir -p " + dirs_s)[0]]


# commands:
@hook
def build(ctx):
    """
    Build src.rpm and make up a list of RPMs to deploy and sign.

    FIXME: ugly code around signkey check.

    :param ctx: Application context object holding parameters
    """
    assert "srpms" in ctx, "'build' command needs srpm paths!"
    assert "repos" in ctx, "No repos defined in given ctx!"

    def csgen():
        for repo, bdist in ctx["repos"]:
            for srpm, noarch in ctx["srpms"]:
                yield mk_cmds_to_build_srpm(repo, srpm, noarch, bdist)

    cs = U.uconcat(cs for cs in cgen())

    if "dryrun" in ctx:
        "commands to run:"
        for c in cs:
            print "# " + c

        sys.exit(0)

    workdir = _init_workdir(ctx.get("workdir", None))
    if workdir:
        ctx["workdir"] = workdir

    logpath = lambda srpm: os.path.join(workdir, "build.%s.log" %
                                        os.path.basename(srpm))
    ps = [SH.run_async(c, logfile=logpath(srpm)) for srpm in srpms]
    return all(stop_async_run(p) for p in ps)


# vim:sw=4:ts=4:et:
