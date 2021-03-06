#
# Copyright (C) 2012 Red Hat, Inc.
# Red Hat Author(s): Masatake YAMATO <yamato@redhat.com>
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
import myrepo.plugin as MP
import logging
import sys

from functools import partial as curry


PRE_HOOKS_PREFIX = "pre_"
POST_HOOKS_PREFIX = "post_"

HOOK_MODULES = MP.load_plugin_modules()


def noop(*args, **kwargs):
    return False


def find_hook(f, prefix, module):
    """
    @param f: function to run commands (see also myrepo.commands)
    @param prefix: prefix of callbacks to run before/after f
    @param module: Plugin module to find hooks
    """
    return getattr(module, prefix + f.func_name, noop)


def hook(f, hmodules=HOOK_MODULES, ignore_exceptions=False,
        pre_prefix=PRE_HOOKS_PREFIX, post_prefix=POST_HOOKS_PREFIX):
    """
    Decorator to run hooks before/after wrapped functions.
    """
    def run(*args, **kwargs):
        def run_pre_post(prefix):
            h = curry(find_hook, f, prefix)
            return [run_in_sandbox(h(m), ignore_exceptions) for m in hmodules]

        def run_in_sandbox(g, ignore_exceptions=True):
            try:
                return g(*args, **kwargs)
            except Exception, e:
                logging.warn(str(e))

                if ignore_exceptions:
                    return e
                else:
                    raise

        run_pre = curry(run_pre_post, pre_prefix)
        run_post = curry(run_pre_post, post_prefix)

        # TODO: What should be done with resutls especially failed ones?
        pre_results = run_pre()
        r = f(*args, **kwargs)
        post_results = run_post()

        return r

    return run


# vim:sw=4:ts=4:et:
