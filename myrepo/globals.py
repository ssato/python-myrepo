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
import os.path
import os


MYREPO_TEMPLATE_PATH = "/usr/share/myrepo/templates"

# common:
_TEMPLATE_PATHS = [os.path.join(MYREPO_TEMPLATE_PATH, "2"),
                   os.path.join(os.curdir, "templates", "2")]

# Logging:
_LOG_FMT = "%(asctime)s [%(levelname)-4s] myrepo: %(message)s"
_LOG_DFMT = "%H:%M:%S"  # too much? "%a, %d %b %Y %H:%M:%S"


# RPM archs:
_RPM_ARCHS = ("i386", "i586", "i686", "x86_64", "ppc", "ia64", "s390",
              "s390x", "noarch")

# timeouts [sec]:
_CONN_LOCAL_TIMEOUT = 3
_CONN_REMOTE_TIMEOUT = 10

# RepoServer defaults:
_CONN_TIMEOUT = 10  # Timeout in seconds to connect to hosts w/ ssh.
_SERVER_TOPDIR = "~%(user)s/public_html/yum"  # Top dir of yum repos.
_SERVER_BASEURL = "http://%(altname)s/~%(user)s/yum"  # Base URL of yum repos.

# Repo defaults:
#   alternatives: "custom-%(name)s"
_REPONAME = "%(name)s-%(server_shortaltname)-%(server_user)s"

# parameters needed for the 'init' / 'genconf' commands:
_KEYDIR = "/etc/pki/rpm-gpg"
_KEYURL = "file://%(keydir)s/RPM-GPG-KEY-%(name)s-%(version)s"


# Commands:  [(abbrev, command, description, require_args?)]
_COMMANDS = [('i', "init", "Initialize yum repo", False),
             ('genc', "genconf",
              "Generate .repo and mock.cfg RPMs for yum repos", False),
             ('u', "update", "Update the meta data of yum repos", False),
             ('b', "build", "Build given SRPMs for the yum repos", True),
             ('d', "deploy",
              "Build and deploy given SRPMs for the yum repos", True)]

# vim:sw=4:ts=4:et:
