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

if logging.getLogger().level < logging.INFO:
    _RPMBUILD += " --verbose"


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

    TODO: Is it better to embed version string in .repo filename ?

    :param repo:  Repo object
    :param tpaths: Template path list :: [str]
    """
    path = os.path.join(workdir, "%s.repo" % repo.name)
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


def build_repodata_srpm(ctx, workdir, tpaths, cmd=_RPMBUILD):
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

    for d in repo["dists"]:  # d :: myrepo.distributed.Distribution
        mpath = os.path.join(workdir, d.mockcfg)
        open(mpath, 'w').write(gen_mock_cfg_content(repo, d, tpaths))

    rc = SH.run(cmd % dict(workdir=workdir, rpmspec=rpmspec),
                stop_on_error=True)
    if rc:
        return glob.glob(workdir, "*.src.rpm")[0]
    else:
        logging.warn("Failed to build yum repodata RPM from " + rpmspec)
        return ""

# vim:sw=4:ts=4:et:
