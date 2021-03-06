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
import myrepo.globals as G
import myrepo.cmds as MC
import myrepo.parser as P
import rpmkit.utils as U
import rpmkit.environ as E

import ConfigParser as configparser
import glob
import itertools
import logging
import optparse
import os
import os.path


_USAGE = """\
%%prog COMMAND [OPTION ...] [SRPM]

Commands:
%s

Examples:
  # initialize your yum repos:
  %%prog init -s yumserver.local -u foo -m foo@example.com -F "John Doe"

  # build SRPM:
  %%prog build packagemaker-0.1-1.src.rpm

  # build SRPM and deploy RPMs and SRPMs into your yum repos:
  %%prog deploy packagemaker-0.1-1.src.rpm
  %%prog d --dists rhel-6-x86_64,fedora-19-x86_64 packagemaker-0.1-1.src.rpm

  # build SRPM has build time dependencies to RPMs in the yum repo:
  %%prog b --dists fedora-19-x86_64 --selfref myrepo-0.1-1.src.rpm\
""" % MC.mk_cmd_helps_text()


def _get_timeout(config):
    """
    >>> _get_timeout(dict(timeout=10, ))
    10
    >>> G._CONN_LOCAL_TIMEOUT == _get_timeout(dict(hostname="localhost", ))
    True
    >>> c = dict(hostname="s.example.com", )
    >>> G._CONN_REMOTE_TIMEOUT == _get_timeout(c)
    True

    :param config: Configuration object :: dict
    """
    timeo = config.get("timeout", None)
    if timeo:
        return timeo

    if U.is_local(config.get("hostname", False)):
        return G._CONN_LOCAL_TIMEOUT
    else:
        return G._CONN_REMOTE_TIMEOUT


def _is_supported(dist):
    """
    >>> _is_supported("fedora-19-x86_64")
    True
    >>> _is_supported("fedora-19-i386")
    True
    >>> _is_supported("fedora-19-armhfp")
    False

    :param dist: Distribution label, e.g. 'fedora-19-x86_64'
    """
    return "x86_64" in dist or "i386" in dist


def _init_by_preset_defaults():
    """

    """
    archs = E.list_archs()
    distributions_full = [d for d in E.list_dists() if _is_supported(d)]
    dists = ["%s-%s" % E.get_distribution()]
    distributions = ["%s-%s" % da for da in itertools.product(dists, archs)]

    h = E.hostname()
    u = E.get_username()
    dists_full = ','.join(distributions_full)
    dists_s = ','.join(distributions)
    (bname, bversion) = E.get_distribution()  # (basename, baseversion)

    cfg = dict(dists=dists_s, dists_full=dists_full, dist_choices=dists_full,
               tpaths=[], workdir=None, dryrun=False, verbosity=1,
               config=None, profile=None,
               hostname=h, altname=None, user=u, topdir=G._SERVER_TOPDIR,
               baseurl=G._SERVER_BASEURL, timeout=None, reponame=G._REPONAME,
               genconf=True, deploy=True,
               fullname=E.get_fullname(), email=E.get_email(),
               keyid=False, repo_params=[], sign=False, selfref=False,
               build=True)

    # Overwrite some parameters:
    cfg["timeout"] = _get_timeout(cfg)

    return cfg


def _init_by_config(config=None, profile=None):
    """
    Initialize default values for options by config files loaded.

    :param config: Config file's path or dir name :: str
    :param profile: Custom profile as needed :: str
    """
    if config is None:
        # Is there case that $HOME is empty?
        home = os.environ.get("HOME", os.curdir)
        confdir = os.environ.get("MYREPO_CONF_PATH", "/etc/myrepo.d")

        confs = ["/etc/myreporc"]
        confs += sorted(glob.glob(os.path.join(confdir, "*.conf")))
        confs += [os.environ.get("MYREPORC", os.path.join(home, ".myreporc"))]
    else:
        if os.path.isdir(config):
            confs = sorted(glob.glob(os.path.join(config, "*.conf")))
        else:
            confs = (config, )

    cparser = configparser.SafeConfigParser()
    loaded = False

    for c in confs:
        if os.path.exists(c):
            logging.info("Loading config: " + c)
            cparser.read(c)
            loaded = True

    if not loaded:
        return {}

    if profile:
        logging.debug("Use profile: " + profile)
        d = cparser.items(profile)
    else:
        logging.debug("Use default profile")
        d = cparser.defaults().iteritems()

    return dict((k, P.parse_conf_value(v)) for k, v in d)


def init(config_path=None, profile=None):
    """
    Initialize config object.
    """
    cfg = _init_by_preset_defaults()
    cfg.update(_init_by_config(config_path, profile))

    return cfg


def opt_parser(usage=_USAGE, conf=None):
    """
    Make up an option parser object.

    >>> p = opt_parser()
    >>> p is not None
    True
    """
    defaults = init(conf)
    dist_choices = defaults["dist_choices"]

    p = optparse.OptionParser(usage)
    p.set_defaults(**defaults)

    cog = optparse.OptionGroup(p, "Common options")
    cog.add_option("", "--dists",
                   help="Comma separated distribution labels including arch "
                        "Options are some of " + dist_choices + " [%default] ")
    cog.add_option("", "--reponame",
                   help="Repository name or format string to generate name, "
                        "e.g. %(name)s-%(server_shortaltname)-%(server_user)s,"
                        " %(name)s-custom. [%default]")
    cog.add_option("-T", "--tpaths", action="append", default=[],
                   help="Specify additional template path one "
                        "by one. These paths will have higher "
                        "priority than the default paths.")
    cog.add_option("-w", "--workdir",
                   help="Working directory to save results and log files. "
                        "Dynamically generated dir will be used by default.")
    cog.add_option("", "--dryrun", action="store_true", help="Dryrun mode")
    cog.add_option("-q", "--quiet", action="store_const", dest="verbosity",
                   const=0, help="Quiet mode")
    cog.add_option("-v", "--verbose", action="store_const", dest="verbosity",
                   const=2, help="Verbose mode")
    p.add_option_group(cog)

    cfog = optparse.OptionGroup(p, "Configuration options")
    cfog.add_option("-C", "--config",
                    help="Configuration file or dir in which config files are")
    cfog.add_option("-P", "--profile",
                    help="Specify configuration profile [none]")
    p.add_option_group(cfog)

    sog = optparse.OptionGroup(p, "Repo server Options")
    sog.add_option("-H", "--hostname",
                   help="Server to provide your yum repos [%default]. "
                        "Please note that you need to specify another "
                        "server name with --altname option if your server "
                        "has alternative name visible for clients.")
    sog.add_option("", "--altname",
                   help="Alternative hostname of the server to provide yum "
                        "repos [%default]. Please note that this may be "
                        "different from the hostname specified with "
                        "--hostname option. The former (--hostname) specifies "
                        "the hostname of the server to connect from your "
                        "admin host while transfering built RPMs, and the "
                        "later (--altname) specifies the hostname of the "
                        "server yum clients will access to. The hostname "
                        "specified with --hostname will be used by default "
                        "if not given.")
    sog.add_option("-u", "--user",
                   help="Your username on the yum repo server [%default].")
    sog.add_option("", "--topdir",
                   help="Repo top dir or its format string [%default].")
    sog.add_option("", "--baseurl",
                   help="Repo base URL or its format string [%default].")
    sog.add_option("", "--timeout", type="int",
                   help="Timeout to connect to the server in seconds "
                        "[%default].")
    p.add_option_group(sog)

    iog = optparse.OptionGroup(p, "Options for 'init' and 'genconf' command")
    iog.add_option("", "--no-genconf", action="store_false", dest="genconf",
                   help="Do not generate yum repo metadata RPMs after "
                        "initialization of the yum repos. NOTE: If you "
                        "specified this option, you have to generate it w/ "
                        "'genconf' sub command of %prog later")
    iog.add_option("", "--no-deploy", action="store_false", dest="deploy",
                   help="Deploy generated yum repo metadata RPMs after "
                        "initialization of the yum repos. This option "
                        "with the above --no-genconf option and must not be "
                        "specified both options at once!")
    iog.add_option("", "--fullname", help="Your full name [%default]")
    iog.add_option("", "--email",
                   help="Your email address or its format string [%default]")
    iog.add_option("", "--keyid", help="Specify the GPG keyid to sign RPMs")
    iog.add_option("", "--repo-param", action="append", dest="repo_params",
                   help="Other .repo file parameter definitions (key=value), "
                        "ex. '--repo-param metadata_expire=7d "
                        "--repo-param failovermethod=priority'.")
    p.add_option_group(iog)

    bog = optparse.OptionGroup(p, "Options for 'build' and 'deploy' command")
    #bog.add_option("", "--sign", action="store_true",
    #               help="Sign built RPMs. You must specify --keyid also.")
    bog.add_option("", "--selfref", action="store_true",
                   help="If specified, %prog will also use the yum repo "
                        "itself to satisfy a portion of buildtime "
                        "dependencies to RPMs available from this repo, "
                        "to build given target SRPM to build.")
    p.add_option_group(bog)

    dog = optparse.OptionGroup(p, "Options for 'deploy' command")
    dog.add_option("", "--no-build", action="store_false", dest="build",
                   help="Do not build given srpm, i.e., the srpm was already "
                        "built and just deploy it")
    p.add_option_group(dog)

    return p


def _find_loglevel(verbosity):
    """
    :param verbosity: Verbosity level = 0 | 1 | 2. It's 1 by default (see also
        ``_init_by_preset_defaults``).
    :return: Logging level

    >>> assert logging.WARN == _find_loglevel(0)  # -q/--quiet
    >>> assert logging.INFO == _find_loglevel(1)  # default
    >>> assert logging.DEBUG == _find_loglevel(2)  # -v/--verbose
    """
    assert verbosity in (0, 1, 2), "Wrong verbosity level ! : %d" % verbosity
    return [logging.WARN, logging.INFO, logging.DEBUG][verbosity]


def find_loglevel(options):
    """
    :param options: An instance of optparse.Values created by parsing args w/
        optparse.OptionParser.parse_args().
    :return: Logging level
    """
    assert isinstance(options, optparse.Values), "Wrong type object passed!"
    return _find_loglevel(options.verbosity)


# vim:sw=4:ts=4:et:
