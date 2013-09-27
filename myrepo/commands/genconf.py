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
from myrepo.commands.utils import assert_repo, assert_ctx_has_keys, \
    setup_workdir
from myrepo.srpm import Srpm

import myrepo.commands.deploy as MCD
import myrepo.repo as MR
import myrepo.shell as MS
import myrepo.utils as MU
import rpmkit.rpmutils as RU

import datetime
import getpass
import glob
import locale
import logging
import os.path
import os
import re
import subprocess
import uuid


_RPM_DIST = ".myrepo"


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

    >>> _check_vars_for_template({'a': 1, 'b': 2}, ['a','b'])
    >>> _check_vars_for_template({}, ['a', ])
    Traceback (most recent call last):
        ...
    AssertionError: Template variable 'a' is missing!
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
    _check_vars_for_template(ctx, ["reponame", "server_altname", "server_user",
                                   "baseurl", "name", "keyid"])

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
    assert_repo(repo)
    ctx["repo"] = repo.as_dict()
    ctx = _setup_extra_template_vars(ctx)

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
    ctx0 = ctx
    ctx0.update(repo.as_dict())
    rfc = gen_repo_file_content(ctx0, tpaths)
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


_CMD_TEMPLATE_0 = """cat << "%s" > %s
%s
%s"""


def mk_write_file_cmd(path, content, eof=None, cfmt=_CMD_TEMPLATE_0):
    """
    :param path: Path of output file
    :param content: Content to be written into output file
    :param eof: The function to generate EOF marker strings for here docuemnts
        or None, that is, it will be generated automatically.

    >>> c = "abc"
    >>> eof = const = lambda: "EOF_123"
    >>> print mk_write_file_cmd("/a/b/c/f.txt", c, eof)
    cat << "EOF_123" > /a/b/c/f.txt
    abc
    EOF_123
    >>>
    """
    eof = gen_eof() if eof is None or not callable(eof) else eof()
    return cfmt % (eof, path, content, eof)


# NOTE: It will override some macros to fix the dir to build srpm, name of
# built srpm and so on.
_CMD_TEMPLATE_1 = """\
cd %s && rpmbuild --define '_srcrpmdir .' --define '_sourcedir .' \
--define '_buildroot .' --define 'dist %s' -bs %s%s"""


def mk_build_srpm_cmd(rpmspec, verbose=False, cfmt=_CMD_TEMPLATE_1,
                      dist=_RPM_DIST):
    """
    :param rpmspec: Path to the RPM SPEC file to build srpm
    :param verbose: Verbosity level

    :return: Command string to build repodata srpm

    >>> ref = "cd /a/b && "
    >>> ref += "rpmbuild --define '_srcrpmdir .' --define '_sourcedir .' "
    >>> ref += "--define '_buildroot .' --define 'dist .myrepo' -bs c.spec"

    >>> s = mk_build_srpm_cmd("/a/b/c.spec")
    >>> assert s == ref, s
    """
    return cfmt % (os.path.dirname(rpmspec), dist, os.path.basename(rpmspec),
                   " --verbose" if verbose else '')


def gen_entoropy():
    """
    Put a load on system and generate entropy needed to generate GPG key.
    """
    cmd = "find / -xdev -type f -exec sha256sum {} >/dev/null \; 2>&1"
    return MS.run_async(cmd)


def find_keyid(signer_name, comment):
    """
    Find out the ID of the GPG key just created to sign RPMs.

    FIXME: Is there any other smarter way to find GPG key ID just created ?
    """
    try:
        out = subprocess.check_output("gpg --list-keys", shell=True)
        prev_line = ""
        for line in out.splitlines():
            if not line:
                continue

            if "%s %s" % (signer_name, comment) in line:
                return re.match(r"^pub +[^/]+/(\w+) .*$",
                                prev_line).groups()[0]
            prev_line = line

    except (subprocess.CalledProcessError, AttributeError):
        return None


def mk_export_gpgkey_files_cmds(keyid, workdir, repos, homedir_opt=''):
    keyfiles = [os.path.join(workdir, "RPM-GPG-KEY-%s" % n) for
                n in MU.uniq(repo.reponame for repo in repos)]

    return ["gpg %s -a --export %s > %s" % (homedir_opt, keyid, f) for
            f in keyfiles]


_GPGKEY_CONF = """\
Key-Type: RSA
Key-Length: 1024
# No subkey, RSA (sign only), to keep compatibility w/ RHEL 5 clients:
Key-Usage: sign
Expire-Date: 0
Name-Real: %(signer_name)s
Name-Comment: %(comment)s
Passphrase: %(passphrase)s
%%no-protection
%%transient-key
%%commit
"""

_RPMMACROS_ADD_0 = """\
%%_signature gpg
%%_gpg_name %s
"""

_RPMMACROS_ADD_1 = _RPMMACROS_ADD_0 + """
%%__gpg_sign_cmd %%{__gpg} \\
gpg --force-v3-sigs --digest-algo=sha1 --batch --no-verbose --no-armor \\
    --passphrase-fd 3 --no-secmem-warning -u "%%{_gpg_name}" \\
    -sbo %%{__signature_filename} %%{__plaintext_filename}
"""


def gen_gpgkey(ctx, rpmmacros="~/.rpmmacros", homedir=None, compat=True,
               passphrase=None):
    """
    Generate and configure GPG key to sign RPMs built.

    :param ctx: Context object to instantiate the template
    :param rpmmacros: .rpmmacros file path
    :param homedir: GPG's home dir (~/.gnupg by default); see also gpg(1)
    :param compat: Keep compatibility of GPG key for older RHEL if True
    :param passphrase: Passphrase for this GPG key

    :return: List of command strings to deploy built RPMs.
    """
    _check_vars_for_template(ctx, ["workdir"])
    workdir = ctx["workdir"]

    if passphrase is None:
        passphrase = getpass.getpass("Passphrase for this GPG key: ")

    homedir_opt = '' if homedir is None else "--homedir " + homedir

    gpgconf = os.path.join(workdir, ".gpg.conf")
    comment = "RPM sign key"
    c = _GPGKEY_CONF % dict(signer_name=ctx["fullname"],
                            comment=comment, passphrase=passphrase)
    logging.info("Generate GPG conf to generate GPG key...")
    open(gpgconf, 'w').write(c)
    os.chmod(gpgconf, 0600)

    sproc = gen_entoropy()
    logging.info("Generate GPG key...")
    MS.run("gpg -v --batch --gen-key %s %s" % (homedir_opt, gpgconf))
    MS.stop_async_run(sproc)
    os.remove(gpgconf)

    keyid = find_keyid(ctx["fullname"], comment)

    logging.info("Export GPG pub key files...")
    for c in mk_export_gpgkey_files_cmds(keyid, workdir, ctx["repos"],
                                         homedir_opt):
        MS.run(c)

    rpmmacros = os.path.expanduser("~/.rpmmacros")

    if os.path.exists(rpmmacros):
        m = "~/.rpmmacros already exists! Edit it manually as needed."
        logging.warn(m)
    else:
        fmt = _RPMMACROS_ADD_1 if compat else _RPMMACROS_ADD_0
        open(rpmmacros, 'w').write(fmt % dict(keyid=keyid, ))
        logging.info("Added GPG key configurations to " + rpmmacros)


def _repo_metadata_srpm_name(repo):
    """
    >>> class Repo(object):
    ...     def __init__(self, reponame):
    ...         self.reponame = reponame
    >>> repo = Repo("fedora-localhost-jdoe")
    >>> _repo_metadata_srpm_name(repo)
    'fedora-localhost-jdoe-release'
    """
    return "%s-release" % repo.reponame


def _repo_metadata_srpm_path(repo, workdir, dist=_RPM_DIST):
    """
    >>> class Repo(object):
    ...     def __init__(self, reponame, version):
    ...         self.reponame = reponame
    ...         self.version = version
    >>> repo = Repo("fedora-localhost-jdoe", "19")
    >>> _repo_metadata_srpm_path(repo, "/a/b/c")
    '/a/b/c/fedora-localhost-jdoe-release-19-1.myrepo.src.rpm'
    """
    fn = "%s-%s-1%s.src.rpm" % (_repo_metadata_srpm_name(repo), repo.version,
                                dist)
    return os.path.join(workdir, fn)


def _mk_repo_metadata_srpm_obj(repo, workdir, dist=_RPM_DIST):
    return Srpm(_repo_metadata_srpm_path(repo, workdir, dist),
                _repo_metadata_srpm_name(repo), repo.version,
                release="1", noarch=True, is_srpm=True, resolved=True)


def prepare_0(repo, ctx, deploy=False, eof=None):
    """
    Make up list of command strings to generate repo's metadata rpms.

    :param repo: myrepo.repo.Repo instance
    :param ctx: Context object to instantiate the template
    :param deploy: Deploy generated yum repo metadata RPMs also if True
    :param eof: The function to generate EOF marker strings for here docuemnts
        or None, that is, it will be generated automatically.

    :return: List of command strings to deploy built RPMs.
    """
    assert_repo(repo)
    _check_vars_for_template(ctx, ["workdir", "tpaths"])

    files = list(gen_repo_files_g(repo, ctx, ctx["workdir"], ctx["tpaths"]))
    rpmspec = files[-1][0]  # FIXME: Ugly hack! (see ``gen_repo_files_g``)

    cs = [mk_write_file_cmd(p, c, eof) for p, c in files] + \
         [mk_build_srpm_cmd(rpmspec, ctx.get("verbose", False))]

    # NOTE: cmd to build srpm must wait for the completion of previous commands
    # to generate files; .repo file, the rpm spec and mock.cfg files:
    c = "\n".join(cs)

    if not deploy:
        return [c]

    srpm = _mk_repo_metadata_srpm_obj(repo, ctx["workdir"])
    dcs = MCD.prepare_0(repo, srpm, build=True)

    assert len(dcs) == 1, \
        "Deploy commands not matched w/ expected: \n" + str(dcs)

    return [MS.join(c, *dcs)]


def prepare(repos, ctx, deploy=False, eof=None):
    """
    Make up list of command strings to update metadata of given repos.
    It's similar to above ``prepare_0`` but applicable to multiple repos.

    :param repos: List of Repo instances
    :param ctx: Context object to instantiate the template
    :param deploy: Deploy generated yum repo metadata RPMs also if True
    :param eof: The function to generate EOF marker strings for here docuemnts
        or None, that is, it will be generated automatically.

    :return: List of command strings to deploy built RPMs.
    """
    return MU.concat(prepare_0(repo, ctx, deploy, eof) for repo in repos)


def _setup_extra_template_vars(ctx):
    if "datestamp" not in ctx:
        ctx["datestamp"] = _datestamp()

    if "fullname" not in ctx:
        ctx["fullname"] = raw_input("Type your full name > ")

    if "email" not in ctx:
        repo = ctx["repos"][0]
        ctx["email"] = "%s@%s" % (repo.server_user, repo.server_altname)

    return ctx


def _mk_dir_if_not_exist(d):
    if not os.path.exists(d):
        logging.info("Create dir: " + d)
        os.makedirs(d)


def _mk_temporary_workdir():
    workdir = setup_workdir()
    logging.info("Create a temporary workdir: " + workdir)
    return workdir


def run(ctx):
    """
    :param ctx: Application context
    :return: True if commands run successfully else False
    """
    assert_ctx_has_keys(ctx, ["repos", "workdir"])

    workdir = ctx.get("workdir", False)
    if workdir:
        _mk_dir_if_not_exist(workdir)
    else:
        ctx["workdir"] = workdir = _mk_temporary_workdir()

    ctx = _setup_extra_template_vars(ctx)
    cs = [c for c in prepare(ctx["repos"], ctx, ctx.get("deploy", False))]

    if ctx.get("dryrun", False):
        for c in cs:
            print c

        return True

    _logfile = lambda: os.path.join(workdir, "%d.log" % os.getpid())
    rc = all(MS.prun(cs, dict(logfile=_logfile, )))

    if not ctx.get("deploy", False):
        prefix = "Created and deployed" if rc else "Failed to create "
        logging.info(prefix + "yum repo config SRPM in: %(workdir)s" % ctx)

    return rc

# vim:sw=4:ts=4:et:
