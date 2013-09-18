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
import rpmkit.environ as E

import difflib
import logging
import os.path
import random
import tempfile


def selfdir():
    return os.path.dirname(__file__)


def template_paths():
    return [os.path.join(selfdir(), "../../templates/2"), ]


def setup_workdir():
    return tempfile.mkdtemp(dir="/tmp", prefix="myrepo-tests")


def log_called(f):
    def run_f(*args, **kwargs):
        logging.info("called: %s, args=%s, kwargs=%s" %
                     (f.func_name, str(args), str(kwargs)))
        return f(*args, **kwargs)

    return run_f


def cleanup_workdir(workdir):
    """
    FIXME: Danger!
    """
    assert os.path.abspath(workdir) != "/"
    os.system("rm -rf " + workdir)


def sample_dist():
    return random.choice(E.list_dists())


def is_base_dist(dist):
    """
    Fixme: Ugly

    >>> is_base_dist("fedora-16-i386")
    True
    >>> is_base_dist("rhel-6-x86_64")
    True
    >>> is_base_dist("fedora-xyz-extras-fedora-16-x86_64")
    False
    """
    return len(dist.split("-")) == 3


def sample_base_dist():
    return random.choice([d for d in E.list_dists() if is_base_dist(d)])


def readfile(f, d=selfdir()):
    return open(os.path.join(d, f)).read()


def diff(s, ref):
    return "\n'" + "\n".join(difflib.unified_diff(s.splitlines(),
                                                  ref.splitlines(),
                                                  'Result', 'Expected')) + "'"

# vim:sw=4:ts=4:et:
