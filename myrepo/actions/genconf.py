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
import myrepo.actions.utils as MAU
import myrepo.repo as MR
import myrepo.shell as MS
import myrepo.utils as MU
import rpmkit.rpmutils as RU

import datetime
import locale
import logging
import os.path
import uuid


def gen_eof():
    return "EOF_%s" % uuid.uuid1()


def _datestamp(d=None):
    """
    Make up a date string to be used in %changelog section of RPM SPEC files.

    >>> _datestamp(datetime.datetime(2013, 7, 31))
    'Wed Jul 31 2013'
    """
    if d is None:
        d = datetime.datetime.now()

    locale.setlocale(locale.LC_TIME, "en_US.UTF-8")
    return datetime.datetime.strftime(d, "%a %b %e %Y")


def _check_vars_for_template(ctx, vars=[]):
    """
    :param ctx: Context object to instantiate the template
    :param vars: Context object to instantiate the template
    """
    for vn in vars:
        assert vn in ctx, "Template variable '%s' is missing!" % vn


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
    # Other candidates: "signkey", "keyurl" and "metadata_expire"
    _check_vars_for_template(ctx, ["reponame", "server_altname", "server_user",
                                   "baseurl", "name"])

    return MU.compile_template("repo_file", ctx, tpaths)


def gen_mock_cfg_content(ctx, tpaths):
    """
    Make up the content of mock.cfg file for given distribution (passed in
    ctx["dist"]) will be put in /etc/yum.repos.d/ and return it.

    :param ctx: Context object to instantiate the template
    :param tpaths: Template path list :: [str]

    :return: String represents the content of mock.cfg file for given repo will
        be put in /etc/mock/ :: str
    """
    _check_vars_for_template(ctx, ["mockcfg", "label", "repo_file_content"])

    return MU.compile_template("mock.cfg", ctx, tpaths)


def gen_rpmspec_content(repo, ctx, tpaths):
    """
    Make up the content of RPM SPEC file for RPMs contain .repo and mock.cfg
    files for given repo ``repo``.

    :param repo: Repo object
    :param ctx: Context object to instantiate the template
    :param tpaths: Template path list :: [str]

    :return: String represents the content of RPM SPEC file :: str
    """
    MAU.assert_repo(repo)

    if "datestamp" not in ctx:
        ctx["datestamp"] = _datestamp()

    if "fullname" not in ctx:
        ctx["fullname"] = raw_input("Type your full name > ")

    if "email" not in ctx:
        ctx["email"] = "%s@%s" % (repo.server_user, repo.server_altname)

    ctx["repo"] = repo.as_dict()
    return MU.compile_template("yum-repodata.spec", ctx, tpaths)


def gen_repo_files_g(repo, ctx, workdir, tpaths):
    """
    Generate .repo, mock.cfg files and the RPM SPEC file for given ``repo`` and
    return list of pairs of the path and the content of each files.

    :param repo: Repo object
    :param ctx: Context object to instantiate the template
    :param workdir: Working dir to build RPMs
    :param tpaths: Template path list :: [str]

    :return: List of pairs of path to file to generate and its content
    """
    rfc = gen_repo_file_content(repo.as_dict(), tpaths)
    yield (os.path.join(workdir, "%s.repo" % repo.reponame), rfc)

    for d in repo.dists:
        label = "%s-%s-%s" % (repo.reponame, repo.version, d.arch)
        rfc2 = rfc.replace("$releasever", repo.version).replace("$basearch",
                                                                d.arch)
        ctx2 = dict(mockcfg=d.mockcfg, label=label, repo_file_content=rfc2)

        yield (os.path.join(workdir, "%s.cfg" % label),
               gen_mock_cfg_content(ctx2, tpaths))

    yield (os.path.join(workdir, "%s-%s.spec" % (repo.reponame, repo.version)),
           gen_rpmspec_content(repo, ctx, tpaths))


_CMD_TEMPLATE_0 = """cat << %s > %s
%s
%s"""


def mk_write_file_cmd(path, content, eof=None, cfmt=_CMD_TEMPLATE_0):
    """
    :param path: Path of output file
    :param content: Content to be written into output file

    >>> c = "abc"
    >>> print mk_write_file_cmd("/a/b/c/f.txt", c, "EOF_123")
    cat << EOF_123 > /a/b/c/f.txt
    abc
    EOF_123
    >>>
    """
    eof = "EOF_%s" % gen_eof() if eof is None or not callable(eof) else eof()

    return cfmt % (eof, path, content, eof)


_CMD_TEMPLATE_1 = """\
cd %s && rpmbuild --define '_srcrpmdir .' --define '_sourcedir .' \
--define '_buildroot .' -bs %s%s"""


def mk_build_srpm_cmd(rpmspec, verbose=False, cfmt=_CMD_TEMPLATE_1):
    """
    :param rpmspec: Path to the RPM SPEC file to build srpm
    :param verbose: Verbosity level

    :return: Command string to build repodata srpm

    >>> ref = "cd /a/b && "
    >>> ref += "rpmbuild --define '_srcrpmdir .' --define '_sourcedir .' "
    >>> ref += "--define '_buildroot .' -bs c.spec"

    >>> s = mk_build_srpm_cmd("/a/b/c.spec")
    >>> assert s == ref, s
    """
    vopt = " --verbose" if verbose else ''
    return cfmt % (os.path.dirname(rpmspec), os.path.basename(rpmspec), vopt)


def prepare_0(repo, ctx, eof=None):
    """
    Make up list of command strings to generate repo's metadata rpms.

    :param repo: myrepo.repo.Repo instance
    :param ctx: Context object to instantiate the template

    :return: List of command strings to deploy built RPMs.
    """
    MAU.assert_repo(repo)
    _check_vars_for_template(ctx, ["workdir", "tpaths"])

    files = list(gen_repo_files_g(repo, ctx, ctx["workdir"], ctx["tpaths"]))
    rpmspec = files[-1][0]  # FIXME: Ugly hack! (see ``gen_repo_files_g``)

    cs = [mk_write_file_cmd(p, c, eof) for p, c in files] + \
         [mk_build_srpm_cmd(rpmspec, ctx.get("verbose", False))]

    # NOTE: cmd to build srpm must wait for the completion of previous commands
    # to generate files; .repo file, the rpm spec and mock.cfg files:
    return [" && ".join(cs)]


def prepare(repos, ctx, eof=None):
    """
    Make up list of command strings to update metadata of given repos.
    It's similar to above ``prepare_0`` but applicable to multiple repos.

    :param repos: List of Repo instances
    :param ctx: Context object to instantiate the template

    :return: List of command strings to deploy built RPMs.
    """
    return MU.concat(prepare_0(repo, ctx, eof) for repo in repos)


def run(ctx):
    """
    :param repos: List of Repo instances

    :return: True if commands run successfully else False
    """
    assert "repos" in ctx, "No repos defined in given ctx!"

    ps = [MS.run_async(c, logfile=False) for c in prepare(ctx["repos"], ctx)]
    return all(MS.stop_async_run(p) for p in ps)


# vim:sw=4:ts=4:et:
