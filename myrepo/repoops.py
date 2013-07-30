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
from logging import INFO

import myrepo.globals as G
import myrepo.utils as U
import rpmkit.memoize as M
import rpmkit.shell as SH

import datetime
import glob
import locale
import logging
import os
import os.path


_SIGN = "rpm --resign --define '_signature gpg' --define '_gpg_name %s' %s"

_RPMBUILD = """rpmbuild \
--define '_srcrpmdir %(workdir)s' \
--define '_sourcedir %(workdir)s' \
--define '_buildroot %(workdir)s' \
-bs %(rpmspec)s"""


def datestamp(d=datetime.datetime.now()):
    locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
    return datetime.datetime.strftime(d, "%a %b %e")


@M.memoize
def gen_repo_file_content(repo, tpaths):
    """
    Make up the content of .repo file for given yum repositoriy ``repo``
    will be put in /etc/yum.repos.d/ and return it.

    :param repo: A myrepo.repo.Repo instance
    :param tpaths: Template path list :: [str]

    :return: String represents the content of .repo file will be put in
        /etc/yum.repos.d/ :: str.
    """
    return U.compile_template("repo_file", repo, tpaths)


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
               base_mock_cfg_path=dist.get_base_mockcfg_path(),
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
    return U.compile_template("yum-repodata.spec", ctx, tpaths)


def sign_rpms_cmd(keyid=None, rpms=[], ask=True, fmt=_SIGN):
    """
    Make up the command string to sign RPMs.

    >>> sign_rpms_cmd("ABCD123", ["a.rpm", "b.rpm"])
    "rpm --resign --define '_signature gpg' --define '_gpg_name ABCD123' a.rpm b.rpm"

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

    :param repo:  Repo object
    :param tpaths: Template path list :: [str]
    """
    reldir = os.path.join(workdir, "etc", "yum.repos.d")
    os.makedirs(reldir)

    path = os.path.join(reldir, "%(name).repo" % repo)
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


def mock_cfg_paths_and_contents_g(repo, workdir, tpaths):
    """
    Return (yield) list of pair of mock.cfg file paths and its content.

    :param repo:  Repo object
    :param workdir: The top dir to generate mock.cfg files
    :param tpaths: Template path list :: [str]

    :return: [(path_of_mock.cfg, content_of_mock.cfg)]
    """
    for dist in repo["dists"]:
        content = gen_mock_cfg_content(repo, dist, tpaths)
        path = os.path.join(workdir, dist.get_mockcfg_path()[1:])

        yield (path, content)


def rpm_build_cmd(ctx, workdir, pname, listfile, tpaths):
    """

    :param ctx: Application context object
    :param workdir: Working dir to build RPMs
    :param pname: RPM package name to build
    :param listfile: List of files to package
    :param tpaths: Template path list :: [str]
    """
    lopt = "--verbose" if logging.getLogger().level < INFO else ""

    ctx["pkgname"] = pname
    ctx["workdir"] = workdir
    ctx["logopt"] = lopt
    ctx["listfile"] = listfile

    return U.compile_template("rpmbuild", ctx, tpaths)


def build_repodata_srpms(ctx, workdir, tpaths, cmd=_RPMBUILD):
    """
    Generate mock.cfg files and corresponding RPMs.

    :param ctx: Application context object
    :param workdir: Working dir to build RPMs
    :param tpaths: Template path list :: [str]
    """
    repo = ctx["repo"]

    for d in repo["dists"]:  # d :: Distribution, dist :: str
        rpmdir = os.path.join(workdir, d.blabel)

        repofile = os.path.join(rpmdir, "%s.repo" % repo["dist"])
        open(repofile, 'w').write(gen_repo_file_content(repo, tpaths))

        mockcfg = os.path.join(rpmdir, "%s.cfg" % d.blabel)
        open(mockcfg, 'w').write(gen_mock_cfg_content(repo, d, tpaths))

        rpmspec = gen_rpmspec(ctx, rpmdir, tpaths)

        rc = SH.run(cmd % dict(workdir=rpmdir, rpmspec=rpmspec),
                    stop_on_error=True)

        if rc:
            yield (d.blabel, rpmdir)
        else:
            logging.warn("Failed to build yum repodata RPM from " + rpmspec)


# FIXME: The following functions are not tested and unittest cases
# should be written.

def build_mock_cfg_srpm(ctx, workdir, tpaths):
    """
    Generate mock.cfg files and corresponding RPMs.
    """
    repo = ctx["repo"]
    cs = []

    for path, content in mock_cfg_paths_and_contents_g(repo, workdir, tpaths):
        open(path, "w").write(content)
        cs.append("%s,rpmattr=%%config(noreplace)" % path)

    c = '\n'.join(cs) + '\n'

    listfile = os.path.join(workdir, "mockcfg.files.list")
    open(listfile, "w").write(c)

    pname = "mock-data-" + repo.name

    rc = SH.run(rpm_build_cmd(ctx, repo, workdir, pname, listfile),
                timeout=ctx["timeout"], stop_on_error=True)

    fmt = "%(wdir)s/mock-data-%(repo)s-%(dver)s/mock-data-*.src.rpm"
    pat = fmt % dict(wdir=workdir, repo=repo["name"], dver=repo["distversion"])
    srpms = glob.glob(pat)

    if not srpms:
        raise RuntimeError("Could not find built src rpms. pattern=" + pat)

    return srpms[0]


def build_release_srpm(repo, workdir):
    """Generate (yum repo) release package.

    :param repo: Repository object
    :param workdir: Working directory in which build rpms
    """
    relpath = gen_repo_file(repo, workdir)
    c = relpath + ",rpmattr=%config\n"

    if repo.signkey:
        keydir = os.path.join(workdir, repo.keydir[1:])
        os.makedirs(keydir)

        rc = SH.run("gpg --export --armor %s > ./%s" % (repo.signkey,
                                                        repo.keyfile),
                    workdir=workdir, timeout=G.MIN_TIMEOUT)
        c += workdir + repo.keyfile + "\n"

    listfile = os.path.join(workdir, "release.files.list")
    open(listfile, "w").write(c)

    pname = repo.name + "-release"

    rc = SH.run(rpm_build_cmd(repo, workdir, listfile, pname),
                repo.user, timeout=G.BUILD_TIMEOUT)

    pattern = "%s/%s-release-%s/%s-release*.src.rpm" % \
        (workdir, repo.name, repo.distversion, repo.name)
    srpms = glob.glob(pattern)

    if not srpms:
        raise RuntimeError("Failed to build src.rpm. pattern=" + pattern)

    return srpms[0]


# vim:sw=4:ts=4:et:
