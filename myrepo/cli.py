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
    :param ctx: Configuration parameters :: dict
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


def main(argv=sys.argv):
    (CMD_INIT, CMD_UPDATE, CMD_BUILD, CMD_DEPLOY, CMD_GEN_CONF_RPMS) = \
        ("init", "update", "build", "deploy", "genconf")

    logformat = "%(asctime)s [%(levelname)-4s] myrepo: %(message)s"
    logdatefmt = "%H:%M:%S"  # too much? "%a, %d %b %Y %H:%M:%S"

    logging.basicConfig(format=logformat, datefmt=logdatefmt)

    p = Conf.opt_parser()
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

    # Hack:
    ctx = options.__dict__.copy()
    ctx["srpms"] = srpms = args[1:]  # List of srpm paths or []

    if srpms:
        if len(srpms) > 1:
            sys.stdout.write("Sorry, myrepo does not support build and/or "
                             "deploy multiple SRPMs yet.")
            sys.exit(0)

        repos = mk_repos(ctx, CMD.is_noarch(srpms[0]))
    else:
        repos = mk_repos(ctx, True)

    for repo in repos:
        ctx["repo"] = repo
        if not getattr(C, cmd)(ctx):
            sys.exit(-1)


if __name__ == '__main__':
    main(sys.argv)


# vim:sw=4:ts=4:et:
