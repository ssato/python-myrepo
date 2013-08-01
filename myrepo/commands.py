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

import myrepo.repoops as RO
import myrepo.shell2 as SH  # Use local copy instead of rpmkit.shell2
import myrepo.utils as U
import rpmkit.memoize as M
import rpmkit.rpmutils as RU

import datetime
import glob
import locale
import logging
import os
import os.path
import subprocess
import tempfile


_SIGN = "rpm --resign --define '_signature gpg' --define '_gpg_name %s' %s"

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


def __setup_workdir(prefix, topdir="/tmp"):
    return tempfile.mkdtemp(dir=topdir, prefix=prefix)


@M.memoize
def gen_repo_file_content(repo, tpaths):
    """
    Make up the content of .repo file for given yum repositoriy ``repo``
    will be put in /etc/yum.repos.d/ and return it.

    NOTE: This function will be called more than twice. So, results of this
    function will be memoized.

    :param repo: A myrepo.repo.Repo instance
    :param tpaths: Template path list :: [str]

    :return: String represents the content of .repo file will be put in
        /etc/yum.repos.d/ :: str.
    """
    return U.compile_template("repo_file", repo.as_dict(), tpaths)


def gen_mock_cfg_content(repo, dist, tpaths):
    """
    Update mock.cfg with addingg repository definitions in
    given content and return it.

    :param repo:  Repo object
    :param dist:  Distribution object
    :param tpaths: Template path list :: [str]

    :return: String represents the content of mock.cfg file for given repo will
        be put in /etc/mock/ :: str
    """
    ctx = dict(dist=dist,
               repo_file_content=gen_repo_file_content(repo, tpaths))

    return U.compile_template("mock.cfg", ctx, tpaths)


def gen_rpmspec_content(ctx, tpaths):
    """
    Make up the content of RPM SPEC file for RPMs contain .repo and mock.cfg
    files for given repo (ctx["repo"]).

    :param ctx: Application context object
    :param tpaths: Template path list :: [str]

    :return: String represents the content of RPM SPEC file :: str
    """
    ctx["datestamp"] = _datestamp()

    return U.compile_template("yum-repodata.spec", ctx, tpaths)


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


def gen_repo_file(repo, workdir, tpaths):
    """
    Generate repo file and return its path.

    TODO: Is it better to embed version string in .repo filename ?

    :param repo:  Repo object
    :param tpaths: Template path list :: [str]
    """
    path = os.path.join(workdir, "%s.repo" % repo.dist)
    open(path, 'w').write(gen_repo_file_content(repo, tpaths))

    return path


def gen_rpmspec(ctx, workdir, tpaths):
    """
    Generate repo file and return its path.

    :param ctx: Application context object
    :param workdir: The top dir to generate output files
    :param tpaths: Template path list :: [str]
    """
    path = os.path.join(workdir, "yum-repodata.spec")
    open(path, 'w').write(gen_rpmspec_content(ctx, tpaths))

    return path


def build_repodata_srpm(ctx, workdir, tpaths):
    """
    Generate .repo file, mock.cfg files and rpm spec for the repo
    (ctx["repo"]), build src.rpm contains them, and returns the path of
    built src.rpm.

    :param ctx: Application context object
    :param workdir: Working dir to build RPMs
    :param tpaths: Template path list :: [str]
    """
    repo = ctx["repo"]

    repofile = gen_repo_file(repo, workdir, tpaths)
    rpmspec = gen_rpmspec(ctx, workdir, tpaths)

    for d in repo.dists:  # d :: myrepo.distributed.Dist
        mpath = os.path.join(workdir, d.mockcfg)
        open(mpath, 'w').write(gen_mock_cfg_content(repo, d, tpaths))

    cmd = "rpmbuild --define '_srcrpmdir .' --define '_sourcedir .' " + \
          "--define '_buildroot .' -bs %s"

    if logging.getLogger().level < logging.INFO:
        cmd += " --verbose"
    else:
        cmd += " 2>/dev/null >/dev/null"

    try:
        # TODO: Fix issues in myrepo.shell2.run and make use of it.
        SH.subprocess.check_call(cmd % os.path.basename(rpmspec),
                                 cwd=workdir, shell=True)

        srpms = glob.glob(os.path.join(workdir, "*.src.rpm"))
        assert srpms, "No src.rpm found in " + workdir
        return srpms[0] if srpms else None

    except:
        logging.warn("Failed to build yum repodata RPM from " + rpmspec)
        return None


def _dists_by_srpm(repo, srpm):
    """
    :param repo: myrepo.repo.Repo object
    :param srpm: Path to src.rpm to build

    :return: List of myrepo.distribution.Dist objects to build given srpm
    """
    return repo.dists[:1] if is_noarch(srpm) else repo.dists


def _build(repo, srpm):
    """
    Build given SRPM file.

    :param repo: myrepo.repo.Repo object
    :param srpm: Path to src.rpm to build

    :return: True if success else False
    """
    largs = [([d.build_cmd(srpm), ], dict(timeout=repo.timeout)) for d in
             _dists_by_srpm(repo, srpm)]

    return SH.prun(largs)


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


# Commands:
@hook
def init(ctx):
    """
    Initialize yum repository.

    :param ctx: Application context object holding parameters
    :return: True if success else False
    """
    repo = ctx["repo"]
    rc = SH.run("mkdir -p " + " ".join(repo.rpmdirs), repo.server_user,
                repo.server_name, timeout=None,
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
    workdir = __setup_workdir("myrepo_" + repo.name + "-release-")

    repo = ctx["repo"]
    srpm = build_repodata_srpm(ctx, workdir, ctx["tpaths"])

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
    repo = ctx["repo"]

    # hack: degenerate noarch rpms
    if repo.multiarch:
        c = "for d in %s; do (cd $d && ln -sf ../%s/*.noarch.rpm ./); done"
        c = c % (" ".join(repo.archs[1:]), repo.primary_arch)

        SH.run(c, repo.server_user, repo.server_name, repo.destdir,
               timeout=None, conn_timeout=repo.server_timeout,
               stop_on_error=True)

    c = "test -d repodata"
    c += " && createrepo --update --deltas --oldpackagedirs . --database ."
    c += " || createrepo --deltas --oldpackagedirs . --database ."

    largs = [([c, repo.server_user, repo.server_name, d, None,
               repo.server_timeout], dict(stop_on_error=True)) for d in
             repo.rpmdirs]

    return SH.prun(largs)


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
