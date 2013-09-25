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

import myrepo.cmds as CM
import myrepo.config as CF
import myrepo.globals as G
import myrepo.parser as P
import myrepo.repo as R
import myrepo.srpm as SRPM

import logging
import sys


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


def mk_repo_server(ctx):
    """
    :param ctx: Configuration parameters :: dict
    :return: myrepo.repo.Server instance

    >>> ctx = dict(hostname="yumrepos-0.m2.local", user="jdoe",
    ...            altname="yumrepos.example.com",
    ...            topdir="~%(user)s/public_html/yum",
    ...            baseurl="http://%(altname)s/~%(user)s/yum",
    ...            timeout=5)
    >>> s = mk_repo_server(ctx)
    >>> isinstance(s, R.Server)
    True
    >>> s.baseurl
    'http://yumrepos.example.com/~jdoe/yum'
    """
    return R.Server(ctx["hostname"], ctx["user"], ctx["altname"],
                    ctx["topdir"], ctx["baseurl"], ctx["timeout"])


def mk_repos(ctx, degenerate=True):
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
        (name, ver, archs, _bdist) = dist

        logging.info("Create repo: name=%s, ver=%s, archs=%s" % dist[:3])

        s = mk_repo_server(ctx)
        yield R.Repo(name, ver, archs, s, ctx["reponame"],
                     selfref=ctx["selfref"])


def modmain(argv):
    """
    :param argv: Argument list for the program
    """
    logging.basicConfig(format=G._LOG_FMT, datefmt=G._LOG_DFMT)

    p = CF.opt_parser()
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
        return 1

    func = CM.find_cmd(args[0])  # @throw CM.CommandNotFoundError

    if options.config or options.profile:
        params = CF.init(options.config, options.profile)
        p.set_defaults(**params)

        # re-parse to overwrite configurations with given options.
        (options, args) = p.parse_args()

    if not options.tpaths:
        options.tpaths = G._TEMPLATE_PATHS

    # Hack:
    ctx = options.__dict__.copy()
    srpms = args[1:]  # List of srpm paths or []

    if srpms:
        if len(srpms) > 1:
            sys.stdout.write("Sorry, myrepo does not support build and/or "
                             "deploy multiple SRPMs yet.")
            return 1

        srpm = SRPM.Srpm(srpms[0])
        srpm.resolve()
        ctx["srpms"] = [srpm]

    ctx["repos"] = repos = list(mk_repos(ctx))

    return func(ctx)  # :: bool


def main(argv=sys.argv):
    sys.exit(0 if modmain(argv) else -1)


if __name__ == '__main__':
    main(sys.argv)


# vim:sw=4:ts=4:et:
