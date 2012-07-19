#
# Copyright (C) 2012 Red Hat, Inc.
# Red Hat Author(s): Masatake YAMATO <yamato@redhat.com>
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
import sys
import os.path
import glob
import logging

mod   = sys.modules['myrepo.hook']
dname = os.path.dirname(mod.__file__)
callback_glob = os.path.join(dname, 'hook_callbacks', '[0-9]*.py*')
callback_modules = map(lambda s: 'myrepo.hook_callbacks.' + s[0:-3],
                       map(os.path.basename, 
                           sorted(glob.glob(callback_glob))))
rcallback_modules = reversed(callback_modules)

for m in callback_modules:
    __import__(m)


def nop(*args, **kwargs):
    return False


def find_entry_point(module_name, func, suffix):
    m = sys.modules[module_name]
    k = func.func_name + suffix;
    return getattr(m, k, False) or nop


def prepare(f):
    def run(*args, **kwargs):
        def make_find_entry_point(suffix):
            return lambda m: find_entry_point(m, f, suffix)

        def run_in_sandbox_pre(c):
            try:
                return c(*args, **kwargs)
            except Exception, e:
                # TODO
                print e
                return e

        def run_in_sandbox_post(c, original_result, pre_result):
            try:
                return c(original_result, pre_result, *args, **kwargs)
            except Exception, e:
                # TODO
                print e
                return e

        def run_pre():
            callback_pre  = map(make_find_entry_point('_pre'), callback_modules)
            return map(run_in_sandbox_pre, callback_pre)

        def run_post(r_original, r_pre):
            callback_post = map(make_find_entry_point('_post'), rcallback_modules)
            map(run_in_sandbox_post, 
                callback_post, 
                map(lambda ignored: r_original, r_pre),
                r_pre)

        results_pre = run_pre()

        try:
            r = f(*args, **kwargs)
        except Exception, e:
            run_post(e, results_pre)
            raise
        else:
            run_post(r, results_pre)
            return r

    return run


# vim:sw=4:ts=4:et:
