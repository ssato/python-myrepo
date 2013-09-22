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


# _COMMANDS = [('i', "init", "Initialize yum repo"),
_CMDS_S = '\n'.join("  %s[%s]\t%s" % (a, c.split(a, 1)[-1], d)
                    for a, c, d, _r in G._COMMANDS)

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
""" % _CMDS_S


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
               keyid='', tpaths=G._TEMPLATE_PATHS, workdir=None,
               quiet=False, verbose=False, debug=False,
               config=None, profile=None,
               hostname=h, altname=h, user=u, topdir=G._SERVER_TOPDIR,
               baseurl=G._SERVER_BASEURL, timeout=None,
               genconf=True, fullname=E.get_fullname(), email=E.get_email(),
               gpgkey="no", repo_params=[], sign=False, selfref=False)

    # Overwrite some parameters:
    cfg["timeout"] = _get_timeout(cfg)

    return cfg


def _init_by_config(config=None, profile=None):
    """
    Initialize default values for options by config files loaded.

    :param config: Config file's path :: str
    :param profile: Custom profile as needed :: str
    """
    if config is None:
        # Is there case that $HOME is empty?
        home = os.environ.get("HOME", os.curdir)

        confs = ["/etc/myreporc"]
        confs += sorted(glob.glob("/etc/myrepo.d/*.conf"))
        confs += [os.environ.get("MYREPORC", os.path.join(home, ".myreporc"))]
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
                        "e.g. %(name)s-%(server_shortaltname)-%(user)s, "
                        "%(name)s-custom. [%default]")
    #cog.add_option("", "--keyid", help="GPG key ID to sign built RPMs")
    cog.add_option("-T", "--tpaths", action="append", default=[],
                   help="Specify additional template path one "
                        "by one. These paths will have higher "
                        "priority than the default paths.")
    cog.add_option("-w", "--workdir",
                   help="Working directory to save results and log files. "
                        "Dynamically generated dir will be used by default.")
    cog.add_option("-q", "--quiet", action="store_true", help="Quiet mode")
    cog.add_option("-v", "--verbose", action="store_true", help="Verbose mode")
    cog.add_option("-D", "--debug", action="store_true", help="Debug mode")
    p.add_option_group(cog)

    cfog = optparse.OptionGroup(p, "Configuration options")
    cfog.add_option("-C", "--config", help="Configuration file")
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
    iog.add_option("", "--fullname", help="Your full name [%default]")
    iog.add_option("", "--email",
                   help="Your email address or its format string [%default]")
    iog.add_option("", "--gpgkey",
                   help="The path to GPG public key file of which key is "
                        "used to sign RPMs deployed, or one of keywords: "
                        "auto, no. If --gpgkey=no, RPMs deployed for this "
                        "repo will not be signed (gpgcheck=0), and if "
                        "--gpgkey=auto, %prog will try to generate a GPG key "
                        "automatically to sign RPMs before deployment. "
                        "[%default]")
    iog.add_option("", "--repo-param", action="append", dest="repo_params",
                   help="Other .repo file parameter definitions (key=value), "
                        "ex. '--repo-param metadata_expire=7d "
                        "--repo-param failovermethod=priority'.")
    p.add_option_group(iog)

    bog = optparse.OptionGroup(p, "Options for 'build' and 'deploy' command")
    #bog.add_option("", "--sign", action="store_true",
    #               help="Sign built RPMs. You must specify --keyid also.")
    bog.add_option("", "--selfref",
                   help="If specified, %prog will also use the yum repo "
                        "itself to satisfy a portion of buildtime "
                        "dependencies to RPMs available from this repo, "
                        "to build given target SRPM to build.")
    p.add_option_group(bog)

    return p

# vim:sw=4:ts=4:et:
