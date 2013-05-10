#
# misc utility routines
#
# Copyright (C) 2011, 2012 Red Hat, Inc.
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
import myrepo.tenjinwrapper as T
import rpmkit.utils as U
import jinja2
import os.path
import os


# Aliases:
typecheck = U.typecheck
is_local = U.is_local


TEMPLATE_PATHS = [
    G.MYREPO_TEMPLATE_PATH, os.path.join(os.curdir, "templates")
]


def compile_template(tmpl, context={}, spaths=TEMPLATE_PATHS):
    """
    :param tmpl: Template file name or (abs or rel) path
    :param context: Context parameters to instantiate the template :: dict
    """
    return T.template_compile(os.path.join("1", tmpl), context, spaths)


def compile_template_2(tmpl, context={}, spaths=TEMPLATE_PATHS):
    """
    :param tmpl: Template file name or (abs or rel) path
    :param context: Context parameters to instantiate the template :: dict
    """
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(spaths))
    return env.get_template(tmpl).render(**context)


# vim:sw=4:ts=4:et:
