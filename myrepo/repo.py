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
from operator import attrgetter

import myrepo.globals as G
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


def _format(fmt_or_val, ctx={}):
    """
    (Format Str | Str) -> Str

    >>> _format("aaa", {})
    'aaa'
    >>> _format("%(a)s", dict(a="123", ))
    '123'

    :param ctx: Context dict object for format strings
    """
    return fmt_or_val % ctx if "%" in fmt_or_val else fmt_or_val


def _foreach_member_of(obj):
    for k, v in obj.__dict__.iteritems():
        if k.startswith('_') or callable(k):
            continue

        yield (k, v)


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
    :param tmpl: Template basename :: str

    :return: String represents the content of RPM SPEC file :: str
    """
    assert "repo" in ctx, "Variable 'repo' is missing in ctx"
    assert isinstance(ctx["repo"], Repo), \
        "ctx['repo'] is not an instance of Repo class"

    if "datestamp" not in ctx:
        ctx["datestamp"] = _datestamp()

    if "fullname" not in ctx:
        ctx["fullname"] = raw_input("Type your name > ")

    if "email" not in ctx:
        ctx["email"] = "%s@%s" % (ctx["repo"].server_user,
                                  ctx["repo"].server_altname)

    return U.compile_template("yum-repodata.spec", ctx, tpaths)


def _write_file(path, content, force=False):
    """
    :param path: Path of output file
    :param content: Content to be written into output file
    :param force: Force overwrite files even if it exists
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


def start_building_srpm_async_g(repo, srpm, logfile=False):
    """
    Start to build src.rpm for each dist (generator version).

    :param repo: Repo object
    :param srpm: Path to src.rpm to build
    :param logfile: Log file path or False (not logged)

    :return: List of multiprocessing.Process instances
    """
    fmt = "Build srpm %s for %s"

    for d in repo.list_dists_to_build_srpm(srpm):
        logging.info(fmt % (srpm, d.label))
        yield SH.run_async(d.build_cmd(srpm), logfile=logfile)


def start_building_srpm_async(repo, srpm, logfile=False):
    """
    Start to build src.rpm for each dist.

    See also the above generator version.

    :param repo: Repo object
    :param srpm: Path to src.rpm to build
    :param logfile: Log file path or False (not logged)

    :return: List of multiprocessing.Process instances
    """
    return list(start_building_srpm_async_g(repo, srpm, logfile))


def wait_building_srpm(repo, srpm, logfile=False, procs=[]):
    """
    Wait to src.rpm are built for dists.

    :param repo: Repo object
    :param srpm: Path to src.rpm to build
    :param logfile: Log file path or False (not logged)
    :param procs: List of multiprocessing.Process instaces to build src.rpm
        for dists. see also above function ``start_building_srpm_async_g``.

    :return: (return_code, {"rpms_to_deploy":, "rpms_to_sign":}
    """
    if not procs:
        procs = start_building_srpm_async(repo, srpm, logfile)

    destdir = repo.destdir
    rpms_to_deploy = []  # :: [(rpm_path, destdir)]
    rpms_to_sign = []
    rc = True

    for i, d in enumerate(repo.list_dists_to_build_srpm(srpm)):
        rpmdir = d.rpmdir()

        if not SH.stop_async_run(procs[i], timeout=None):
            logging.warn("Failed to build srpm %s for %s" % (srpm, d.label))
            rc = False

        srpms_to_copy = glob.glob(os.path.join(rpmdir, "*.src.rpm"))
        assert srpms_to_copy, "Could not find src.rpm in " + rpmdir

        srpm_to_copy = srpms_to_copy[0]
        rpms_to_deploy.append((srpm_to_copy, os.path.join(destdir, "sources")))

        brpms = [f for f in glob.glob(os.path.join(rpmdir, "*.rpm"))
                 if not f.endswith(".src.rpm")]

        m = "Found rpms: " + str([os.path.basename(f) for f in brpms])
        logging.debug(m)

        for p in brpms:
            rpms_to_deploy.append((p, os.path.join(destdir, d.arch)))

        rpms_to_sign += brpms

    return (rc, dict(rpms_to_deploy=rpms_to_deploy,
                     rpms_to_sign=rpms_to_sign))


def build_srpm(repo, srpm, logfile=False):
    """
    Build src.rpm and make up a list of RPMs to deploy and sign.

    FIXME: Ugly code around signkey check and setting RPMs to deploy.

    :param repo: Repo object
    :param srpm: Path to src.rpm to build

    :return: (return_code, {"rpms_to_deploy":, "rpms_to_sign":}
    """
    return wait_building_srpm(repo, srpm)


class Server(object):
    """
    >>> s = Server("localhost", "jdoe",
    ...                baseurl="file:///home/%(user)s/public_html/yum")
    >>> s.name, s.user, s.altname, s.shortname, s.shortaltname
    ('localhost', 'jdoe', 'localhost', 'localhost', 'localhost')
    >>> s.topdir
    '~jdoe/public_html/yum'
    >>> s.baseurl
    'file:///home/jdoe/public_html/yum'

    >>> s = Server("yumrepos.local", "jdoe", "yumrepos.example.com")
    >>> s.name, s.user, s.altname, s.shortname, s.shortaltname
    ('yumrepos.local', 'jdoe', 'yumrepos.example.com', 'yumrepos', 'yumrepos')
    >>> s.baseurl
    'http://yumrepos.example.com/~jdoe/yum'

    >>> s.is_local
    False

    >>> s = Server("localhost", "jdoe", baseurl="file:///tmp")
    >>> s.baseurl
    'file:///tmp'
    >>> s.is_local
    True
    """

    def __init__(self, name, user, altname=None, topdir=G._SERVER_TOPDIR,
                 baseurl=G._SERVER_BASEURL, timeout=G._CONN_TIMEOUT):
        """
        :param name: FQDN or hostname of the server provides yum repos
        :param user: User name on the server to provide yum repos
        :param altname: Alternative hostname (FQDN) for client access
        :param topdir: Top dir or its format string of yum repos to serve RPMs.
        :param baseurl: Base url or its format string of yum repos
        :param timeout: SSH connection timeout to this server
        """
        self.name = name
        self.user = user
        self.altname = name if altname is None else altname
        self.timeout = timeout  # It will be ignored if this host is localhost.

        self.shortname = self._mk_shortname(self.name)
        self.shortaltname = self._mk_shortname(self.altname)

        ctx = dict(name=name, user=user, altname=self.altname, timeout=timeout,
                   shortname=self.shortname, shortaltname=self.shortaltname)

        # The followings may be format strings.
        self.topdir = _format(topdir, ctx)
        self.baseurl = _format(baseurl, ctx)

        self.is_local = SH.is_local(self.name)

    def _mk_shortname(self, name, sep='.'):
        return name.split(sep)[0] if sep in name else name

    def deploy_cmd(self, src, dst):
        """
        Make up and and return command strings to deploy objects from ``src``
        to ``dst`` on the server.

        :param src: Copying source (path) :: str
        :param dst: Copying destination (path) :: str

        :return: command string to deploy objects :: str
        """
        if self.is_local:
            if "~" in dst:
                dst = os.path.expanduser(dst)

            return "cp -a %s %s" % (src, dst)
        else:
            return "scp -p %s %s@%s:%s" % (src, self.user, self.name, dst)


class Dist(object):
    """
    >>> d = Dist("fedora-19", "x86_64")
    >>> d.dist, d.arch, d.label
    ('fedora-19', 'x86_64', 'fedora-19-x86_64')
    >>> d.mockcfg
    'fedora-19-x86_64.cfg'
    """

    def __init__(self, dist, arch):
        """
        :param dist: ${name}-${version}, e.g. "fedora-19", "rhel-6".
        :param arch: Architecture, e.g. "i386", "x86_64"
        """
        self.dist = dist
        self.arch = arch

        self.label = "%s-%s" % (dist, arch)
        self.mockcfg = "%s.cfg" % self.label

    def rpmdir(self):
        """Dir to save built RPMs.
        """
        return "/var/lib/mock/%s/result" % self.label

    def build_cmd(self, srpm):
        return _build_cmd(self.label, srpm)


class Repo(object):
    """
    Yum repository.

    >>> s = Server("yumrepos-1.local", "jdoe", "yumrepos.example.com")
    >>> repo = Repo("fedora", 19, ["x86_64", "i386"], s,
    ...             reponame="%(name)s-%(server_shortaltname)s")

    >>> repo.name, repo.version, repo.archs
    ('fedora', '19', ['x86_64', 'i386'])

    >>> repo.server_name, repo.server_altname
    ('yumrepos-1.local', 'yumrepos.example.com')
    >>> repo.server_shortname, repo.server_shortaltname,
    ('yumrepos-1', 'yumrepos')
    >>> repo.server_baseurl
    'http://yumrepos.example.com/~jdoe/yum'

    >>> repo.multiarch, repo.primary_arch
    (True, 'x86_64')

    >>> repo.dist, repo.label
    ('fedora-19', 'fedora-19-x86_64')

    >>> repo.subdir, repo.destdir
    ('fedora/19', '~jdoe/public_html/yum/fedora/19')
    >>> repo.baseurl
    'http://yumrepos.example.com/~jdoe/yum'
    >>> repo.url
    'http://yumrepos.example.com/~jdoe/yum/fedora/19'
    >>> repo.rpmdirs  # doctest: +NORMALIZE_WHITESPACE
    ['~jdoe/public_html/yum/fedora/19/sources',
     '~jdoe/public_html/yum/fedora/19/x86_64',
     '~jdoe/public_html/yum/fedora/19/i386']

    >>> repo.reponame
    'fedora-yumrepos'
    """

    def __init__(self, name, version, archs, server, reponame=G._REPONAME):
        """
        :param name: Build target distribution name, fedora or rhel.
        :param version: Version string or number :: int
        :param archs: List of architectures, e.g. ["x86_64", "i386"]
        :param server: Server object :: myrepo.repo.Server
        :param reponame: This repo's name or its format string, e.g.
            "fedora-custom", "%(name)s-%(server_shortaltname)s"
        """
        self.name = name
        self.version = str(version)
        self.archs = archs
        self.server = server

        # Setup aliases of self.server.<key>:
        for k, v in _foreach_member_of(server):
            setattr(self, "server_" + k, v)

        self.multiarch = "i386" in self.archs and "x86_64" in self.archs
        self.primary_arch = "x86_64" if self.multiarch else self.archs[0]

        if self.multiarch:
            self.archs = [self.primary_arch] + \
                         [a for a in archs if a != self.primary_arch]

        self.dist = "%s-%s" % (self.name, self.version)
        self.label = "%s-%s" % (self.dist, self.primary_arch)

        self.subdir = os.path.normpath(os.path.join(self.name, self.version))
        self.destdir = os.path.normpath(os.path.join(self.server_topdir,
                                                     self.subdir))
        self.baseurl = self.server_baseurl
        self.url = os.path.join(self.baseurl, self.subdir)

        self.rpmdirs = [os.path.join(self.destdir, d) for d in
                        ["sources"] + self.archs]

        self.reponame = self._format(reponame)
        self.rootbase = "%s-%s" % (self.reponame, self.version)
        self.dists = [Dist(self.dist, a) for a in self.archs]

    def as_dict(self):
        return self.__dict__

    def _format(self, fmt_or_val):
        return _format(fmt_or_val, self.as_dict())

    def mock_root(self, dist):
        """
        :param dist: Dist object
        """
        return "%s-%s" % (self.rootbase, dist.arch)

    def list_dists_to_build_srpm(self, srpm):
        """
        List dists to build given src.rpm.

        :param srpm: Path to src.rpm to build
        :return: List of Dist objects to build given srpm
        """
        return self.dists[:1] if RU.is_noarch(srpm) else self.dists

    def deploy_cmd(self, src, dst):
        """
        Make up and and return command strings to deploy objects from ``src``
        to ``dst`` on the server.

        :param src: Copying source (path) :: str
        :param dst: Copying destination (path) :: str

        :return: command string to deploy objects :: str
        """
        return self.server.deploy_cmd(src, dst)

# vim:sw=4:ts=4:et:
