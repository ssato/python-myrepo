#
# Generate yum repo config RPMs contain .repo and mock.cfg files.
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
import myrepo.shell as SH
import myrepo.utils as U
import rpmkit.rpmutils as RU

import datetime
import glob
import locale
import logging
import os.path


def _datestamp(d=datetime.datetime.now()):
    """
    Make up a date string to be used in %changelog section of RPM SPEC files.

    >>> _datestamp(datetime.datetime(2013, 7, 31))
    'Wed Jul 31 2013'
    """
    locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
    return datetime.datetime.strftime(d, "%a %b %e %Y")


def gen_repo_file_content(ctx, tpaths):
    """
    Make up the content of .repo file for given yum repositoriy ``repo``
    will be put in /etc/yum.repos.d/ and return it.

    NOTE: This function will be called more than twice. So, results of this
    function will be memoized.

    :param ctx: Context object to instantiate the template
    :param tpaths: Template path list :: [str]

    :return: String represents the content of .repo file will be put in
    /etc/yum.repos.d/ :: str.
    """
    return U.compile_template("repo_file", ctx, tpaths)


def gen_mock_cfg_content(ctx, tpaths):
    """
    Make up the content of mock.cfg file for given distribution (passed in
    ctx["dist"]) will be put in /etc/yum.repos.d/ and return it.

    :param ctx: Context object to instantiate the template
    :param tpaths: Template path list :: [str]

    :return: String represents the content of mock.cfg file for given repo will
        be put in /etc/mock/ :: str
    """
    assert "repo_file_content" in ctx, \
        "Template variable 'repo_file_content' is missing!"

    return U.compile_template("mock.cfg", ctx, tpaths)


def gen_rpmspec_content(ctx, tpaths):
    """
    Make up the content of RPM SPEC file for RPMs contain .repo and mock.cfg
    files for given repo (ctx["repo"]).

    :param ctx: Context object to instantiate the template
    :param tpaths: Template path list :: [str]

    :return: String represents the content of RPM SPEC file :: str
    """
    assert "repo" in ctx, "Variable 'repo' is missing in ctx"
    assert isinstance(ctx["repo"], MR.Repo), \
        "ctx['repo'] is not an instance of Repo class"

    if "datestamp" not in ctx:
        ctx["datestamp"] = _datestamp()

    if "fullname" not in ctx:
        ctx["fullname"] = raw_input("Type your full name > ")

    if "email" not in ctx:
        ctx["email"] = "%s@%s" % (ctx["repo"].server_user,
                                  ctx["repo"].server_altname)

    return U.compile_template("yum-repodata.spec", ctx, tpaths)


def _write_file(path, content, force=False):
    """
    :param path: Path of output file
    :param content: Content to be written into output file
    :param force: Force overwrite files even if it exists

    :raise IOError: if failed to write ``content`` to the file ``path``.
    """
    if os.path.exists(path) and not force:
        logging.info("The output '%s' already exists. Do nothing")
    else:
        logging.info("Generate file: " + path)
        open(path, 'w').write(content)


def gen_repo_files_g(repo, workdir, tpaths, force=False):
    """
    Generate .repo and mock.cfg files for given ``repo`` and return these
    paths (generator version).

    :param repo: Repo object
    :param workdir: Working dir to build RPMs
    :param tpaths: Template path list :: [str]
    :param force: Force overwrite files even if it exists

    :return: List of generated file's path
    """
    rfc = gen_repo_file_content(repo.as_dict(), tpaths)
    path = os.path.join(workdir, "%s.repo" % repo.reponame)

    _write_file(path, rfc, force)
    yield path

    for d in repo.dists:
        root = repo.mock_root(d)
        rfc2 = rfc.replace("$releasever", repo.version).replace("$basearch",
                                                                d.arch)
        ctx = dict(mock_root=root, repo_file_content=rfc2,
                   base_mockcfg=("%s-%s.cfg" % (d.dist, d.arch)))

        path = os.path.join(workdir, "%s.cfg" % root)
        c = gen_mock_cfg_content(ctx, tpaths)

        _write_file(path, c, force)
        yield path


def gen_repo_files(repo, workdir, tpaths, force=False):
    """
    Generate .repo and mock.cfg files for given ``repo`` and return these
    paths.

    :param repo: Repo object
    :param workdir: Working dir to build RPMs
    :param tpaths: Template path list :: [str]
    :param force: Force overwrite files even if it exists

    :return: List of path to the yum repo metadata files :: [str]
    """
    return list(gen_repo_files_g(repo, workdir, tpaths, force))


def gen_rpmspec(ctx, workdir, tpaths, force=False):
    """
    Generate RPM SPEEC file to package yum repo metadata files (.repo and
    mock.cfg) and return its path.

    :param ctx: Context object to instantiate the template
    :param workdir: Working dir to save RPM SPEC output
    :param tpaths: Template path list :: [str]
    :param force: Force overwrite files even if it exists

    :return: List of path to the yum repo metadata files :: [str]
    """
    path = os.path.join(workdir, "%s-%s.spec" % (ctx["repo"].reponame,
                                                 ctx["repo"].version))
    c = gen_rpmspec_content(ctx, tpaths)
    _write_file(path, c, force)

    return path


def build_repodata_srpm(ctx, workdir, tpaths, logfile=None):
    """
    Generate repodata files, .repo file, mock.cfg files and rpm spec, for given
    yum repo (ctx["repo"]), package them and build src.rpm, and returns the
    path of built src.rpm.

    :param ctx: Context object to instantiate the template
    :param workdir: Working dir to build RPMs
    :param tpaths: Template path list :: [str]

    :return: Path to the built src.rpm file or None (failed to build it)
    """
    assert "repo" in ctx, "Variable 'repo' is missing in ctx"
    assert os.path.realpath(workdir) != os.path.realpath(os.curdir), \
        "Workdir must not be curdir!"

    files = gen_repo_files(ctx["repo"], workdir, tpaths)
    f = gen_rpmspec(ctx, workdir, tpaths)

    if logfile is None:
        logfile = os.path.join(workdir, "build_repodata_srpm.log")

    vopt = " --verbose" if logging.getLogger().level < logging.INFO else ''

    c = "rpmbuild --define '_srcrpmdir .' --define '_sourcedir .' " + \
        "--define '_buildroot .' -bs %s%s" % (os.path.basename(f), vopt)

    if SH.run(c, workdir=workdir, logfile=logfile):
        srpms = glob.glob(os.path.join(workdir, "*.src.rpm"))
        assert srpms, "No src.rpm found in " + workdir

        return srpms[0] if srpms else None
    else:
        logging.warn("Failed to build yum repodata RPM from " + f)
        return None


# vim:sw=4:ts=4:et:
