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

  # build SRPM and deploy RPMs and SRPMs into your yum repo.
  #
  # Here, fedora-19-x86_64 is base distribution and my-fedora-19-x86_64 is
  # build target distribution:
  #
  %%prog d --dists fedora-17-x86_64:my-fedora-17-x86_64 myrepo-0.1-1.src.rpm\
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


def _init_by_defaults():
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

    cfg = dict(hostname=h, user=u, altname=h, topdir=G._SERVER_TOPDIR,
               baseurl=G._SERVER_BASEURL, timeout=None,
               dists_full=dists_full, dists=dists_s, dist_choices=dists_full,
               basename=bname, subdir=G._SUBDIR,
               signkey=G._SIGNKEY, keydir=G._KEYDIR, keyurl=G._KEYURL,
               genconf=True, email=E.get_email(), fullname=E.get_fullname(),
               config=None, profile=None, tpaths=G._TEMPLATE_PATHS,
               verbose=False, quiet=False, debug=False)

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
    cfg = _init_by_defaults()
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
                        "(optionally w/ build (mock) distribution label). "
                        "Options are some of " + dist_choices +
                        " [%default] and these combinations: e.g. "
                        "fedora-19-x86_64, "
                        "rhel-6-x86_64:my-custom-addon-rhel-6-x86_64")
    cog.add_option("-T", "--tpaths", action="append", default=[],
                   help="Specify additional template path one "
                        "by one. These paths will have higher "
                        "priority than default paths.")

    cog.add_option("-q", "--quiet", action="store_true", help="Quiet mode")
    cog.add_option("-v", "--verbose", action="store_true", help="Verbose mode")
    cog.add_option("-D", "--debug", action="store_true", help="Debug mode")
    p.add_option_group(cog)

    cfog = optparse.OptionGroup(p, "Configuration options")
    cfog.add_option("-C", "--config", help="Configuration file")
    cfog.add_option("-P", "--profile",
                    help="Specify configuration profile [none]")
    p.add_option_group(cfog)

    sog = optparse.OptionGroup(p, "(Repo) server Options")
    sog.add_option("-H", "--hostname",
                   help="Server to provide your yum repos. Please note that "
                        "you need to specify another server name with "
                        "--altname option if you server has alternative name "
                        " for clients, Localhost will be used by default")
    sog.add_option("", "--altname",
                   help="Alternative hostname of the server to provide yum "
                        "repos. Please note that this is different from "
                        "the hostname specified with --hostname option. "
                        "The former (--hostname) specifies the hostname of "
                        "the server to connect from your workstation, and "
                        "the later (--altname) specifies the hostname of "
                        "the server yum clients access to. The hostname "
                        "specified with --hostname will be used by default.")
    sog.add_option("-u", "--user",
                   help="Your username on the yum repo server [%default]")
    sog.add_option("", "--topdir",
                   help="Repo top dir or its format string [%default]")
    sog.add_option("", "--baseurl",
                   help="Repo base URL or its format string [%default]")
    sog.add_option("", "--timeout", type="int",
                   help="Timeout to connect to the server in seconds "
                        "[%default]")
    p.add_option_group(sog)

    iog = optparse.OptionGroup(p, "Options for 'init' command")
    iog.add_option("", "--no-genconf", action="store_false", dest="genconf",
                   help="Do not generate yum repo metadata RPMs after "
                        "initialization of yum repos.")
    iog.add_option("", "--name",
                   help="Name of your yum repo or its format string "
                        "[%default].")
    iog.add_option("", "--basename",
                   help="Base distribution name or not set (None).")
    iog.add_option("", "--subdir", help="Repository sub dir name [%default]")
    iog.add_option("", "--email",
                   help="Your email address or its format string [%default]")
    iog.add_option("", "--fullname", help="Your full name [%default]")
    iog.add_option("", "--signkey",
                   help="GPG key ID if signing RPMs to deploy")
    iog.add_option("", "--keydir", help="GPG key store directory [%default]")
    iog.add_option("", "--keyurl", help="GPG key URL [%default]")
    p.add_option_group(iog)

    return p

# vim:sw=4:ts=4:et:
