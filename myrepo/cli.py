#
# CLI module
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
from itertools import groupby
from operator import itemgetter

import myrepo.commands as CMD
import myrepo.config as Conf
import myrepo.globals as G
import myrepo.parser as P
import myrepo.repo as R

import bunch as B
import logging
import multiprocessing
import optparse
import sys
import time


def _listify_arch(dname, dver, darch, bdist):
    """
    >>> _listify_arch('fedora', '16', 'x86_64', 'fedora-16')
    ['fedora', '16', ['x86_64'], 'fedora-16']
    """
    return [dname, dver, [darch], bdist]


def _degenerate_dists_g(dists):
    """
    Degenerate dists by bdist. (It is needed to avoid building noarch srpms
    multiple times.)

    >>> d0 = ('fedora', '16', 'x86_64', 'fedora-16')
    >>> d1 = ('fedora', '16', 'i386', 'fedora-16')
    >>> d2 = ('rhel', '6', 'x86_64', 'rhel-6')

    >>> list(_degenerate_dists_g([d0, d1]))
    [('fedora', '16', ['x86_64', 'i386'], 'fedora-16')]

    >>> ds2 = [
    ...    ('fedora', '16', ['x86_64', 'i386'], 'fedora-16'),
    ...    ('rhel', '6', ['x86_64'], 'rhel-6')
    ... ]
    >>> list(_degenerate_dists_g([d0, d1, d2])) == ds2
    True
    """
    key_f = itemgetter(3)  # to extract bdist from dist.
    bds = [(bdist, list(ds)) for bdist, ds in groupby(dists, key_f)]

    for bd in bds:
        bdist = bd[0]
        dists = bd[1]

        dist0 = dists[0]
        archs = [d[2] for d in dists]

        (dname, dver) = dist0[:2]

        yield (dname, dver, archs, bdist)


def mk_repos(ctx, degenerate=False):
    """
    :param ctx: Configuration parameters :: B.Bunch
    :param degenerate:  Is the dists to be degenerated?

    see also: myrepo.parser.parse_dists_option
    """
    dists_s = ctx["dists"]
    logging.debug("ctx['dists']=" + dists_s)

    # dists :: [(dist_name, dist_ver, dist_arch, bdist)]
    dists = P.parse_dists_option(dists_s)
    logging.debug("dists: " + str(dists))

    if degenerate:
        dists = _degenerate_dists_g(dists)
    else:
        dists = (_listify_arch(*d) for d in dists)

    for dist in dists:
        (dname, dver, archs, bdist) = dist

        logging.debug("Creating repo: dname=%s, dver=%s, archs=%s, "
                      "bdist=%s" % (dname, dver, archs, bdist))

        s = R.RepoServer(ctx["hostname"], ctx["user"], ctx["altname"],
                         ctx["topdir"], ctx["baseurl"], ctx["timeout"])
        yield R.Repo(dname, dver, archs, ctx["base_name"], s, bdist,
                     ctx["subdir"], ctx["signkey"], ctx["keydir"],
                     ctx["keyurl"])


def opt_parser():
    defaults = Conf.init()
    distribution_choices = defaults["distribution_choices"]

    p = optparse.OptionParser("""%prog COMMAND [OPTION ...] [SRPM]

Commands: i[init], b[uild], d[eploy], u[pdate], genc[onf]

Examples:
  # initialize your yum repos:
  %prog init -s yumserver.local -u foo -m foo@example.com -F "John Doe"

  # build SRPM:
  %prog build packagemaker-0.1-1.src.rpm

  # build SRPM and deploy RPMs and SRPMs into your yum repos:
  %prog deploy packagemaker-0.1-1.src.rpm
  %prog d --dists rhel-6-x86_64 packagemaker-0.1-1.src.rpm

  # build SRPM and deploy RPMs and SRPMs into your yum repo; fedora-17-x86_64
  # is base distribution and my-fedora-17-x86_64 is target distribution:
  %prog d --dists fedora-17-x86_64:my-fedora-17-x86_64 myrepo-0.1-1.src.rpm
  """)

    for k in ("verbose", "quiet", "debug"):
        if not defaults.get(k, False):
            defaults[k] = False

    p.set_defaults(**defaults)

    p.add_option("-C", "--config", help="Configuration file")
    p.add_option("-P", "--profile",
                 help="Specify configuration profile [%default]")
    p.add_option("-T", "--tpaths", action="append", default=[],
                 help="Specify additional template path one "
                      "by one. These paths will have higher "
                      "priority than default paths."),
    p.add_option("", "--timeout", type="int",
                 help="Timeout [sec] for each operations [%default]")

    p.add_option("-s", "--server",
                 help="HTTP/FTP Server to provide your yum repos. "
                      "Localhost will be used by default if not specified.")
    p.add_option("-u", "--user",
                 help="Your username on that yum repo server [%default]")
    p.add_option("", "--dists",
                 help="Comma separated distribution labels including arch "
                      "(optionally w/ build (mock) distribution label). "
                      "Options are some of " + distribution_choices +
                      " [%default] and these combinations: e.g. "
                      "fedora-16-x86_64, "
                      "rhel-6-i386:my-custom-addon-rhel-6-i386")

    p.add_option("-q", "--quiet", action="store_true", help="Quiet mode")
    p.add_option("-v", "--verbose", action="store_true", help="Verbose mode")
    p.add_option("", "--debug", action="store_true", help="Debug mode")

    iog = optparse.OptionGroup(p, "Options for 'init' command")
    iog.add_option('', "--name",
                   help="Name of your yum repo or its format string "
                        "[%default].")
    iog.add_option("", "--subdir", help="Repository sub dir name [%default]")
    iog.add_option("", "--topdir",
                   help="Repository top dir or its format string [%default]")
    iog.add_option('', "--baseurl",
                   help="Repository base URL or its format string [%default]")
    iog.add_option("-m", "--email",
                   help="Your email address or its format string [%default]")
    iog.add_option("-F", "--fullname", help="Your full name [%default]")
    iog.add_option('', "--signkey",
                   help="GPG key ID if signing RPMs to deploy")
    iog.add_option('', "--no-genconf", action="store_false", dest="genconf",
                   help="Do not run genconf command after initialization "
                        "finished")
    p.add_option_group(iog)

    return p


def _action(func, args):
    func(*args)


def do_command_org(cmd, repos_g, srpm=None):
    """
    :param cmd: sub command name :: str
    :param repos_g: Repository objects (generator)
    :param srpm: path to the target src.rpm :: str
    """
    f = getattr(CMD, cmd)
    jobs = []

    for repo in repos_g:
        rest_args = (repo, ) if srpm is None else (repo, srpm)

        proc = multiprocessing.Process(target=_action, args=(f, rest_args))
        proc.start()

        jobs.append(proc)

    time.sleep(G.MIN_TIMEOUT)

    for proc in jobs:
        # it will block.
        proc.join(G.BUILD_TIMEOUT)

        # Is there any possibility thread still live?
        if proc.is_alive():
            logging.info("Terminating the proc: " + str(proc.pid))

            proc.join(G.BUILD_TIMEOUT)  # one more wait
            proc.terminate()


def do_command(cmd, ctx, repos_g, timeout=G.BUILD_TIMEOUT):
    """
    :param cmd: sub command name :: str
    :param repos_g: Repository objects (generator)
    """
    for repo in repos_g:
        ctx.repo = repo
        getattr(CMD, cmd)(ctx)


def main(argv=sys.argv):
    (CMD_INIT, CMD_UPDATE, CMD_BUILD, CMD_DEPLOY, CMD_GEN_CONF_RPMS) = \
        ("init", "update", "build", "deploy", "genconf")

    logformat = "%(asctime)s [%(levelname)-4s] myrepo: %(message)s"
    logdatefmt = "%H:%M:%S"  # too much? "%a, %d %b %Y %H:%M:%S"

    logging.basicConfig(format=logformat, datefmt=logdatefmt)

    p = opt_parser()
    (options, args) = p.parse_args(argv[1:])

    if options.verbose:
        loglevel = logging.INFO
    elif options.debug:
        loglevel = logging.DEBUG
    elif options.quiet:
        loglevel = logging.ERROR
    else:
        loglevel = logging.WARN

    logging.getLogger().setLevel(loglevel)

    if not args:
        p.print_usage()
        sys.exit(1)

    def assert_no_arg(args):
        assert len(args) < 2, "'%s' command requires no arguments" % cmd

    def assert_arg(args):
        assert len(args) >= 2, \
            "'%s' command requires an argument to specify srpm[s]" % cmd

    a0 = args[0]
    if a0.startswith('i'):
        cmd = CMD_INIT
        assert_no_arg(args)

    elif a0.startswith('u'):
        cmd = CMD_UPDATE
        assert_no_arg(args)

    elif a0.startswith('b'):
        cmd = CMD_BUILD
        assert_arg

    elif a0.startswith('d'):
        cmd = CMD_DEPLOY
        assert_arg

    elif a0.startswith("genc"):
        cmd = CMD_GEN_CONF_RPMS
        assert_no_arg(args)
    else:
        logging.error(" Unknown command '%s'" % a0)
        sys.exit(1)

    if options.config or options.profile:
        params = Conf.init(options.config, options.profile)
        p.set_defaults(**params)

        # re-parse to overwrite configurations with given options.
        (options, args) = p.parse_args()

    ctx = B.Bunch(options.__dict__.copy())
    ctx.srpms = args[1:]  # List of srpm paths or []

    if ctx.srpms:
        if len(ctx.srpms) > 1:
            sys.stdout.write("Sorry, myrepo does not support build and/or "
                             "deploy multiple SRPMs yet.")
            sys.exit(0)

        repos_g = mk_repos(ctx, CMD.is_noarch(ctx.srpms[0]))
    else:
        repos_g = mk_repos(ctx, True)

    sys.exit(do_command(cmd, ctx, repos_g))


if __name__ == '__main__':
    main(sys.argv)


# vim:sw=4:ts=4:et:
