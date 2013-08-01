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
MYREPO_TEMPLATE_PATH = "/usr/share/myrepo/templates"

# timeouts [sec]:
(REMOTE_TIMEOUT, BUILD_TIMEOUT, LOCAL_TIMEOUT, MIN_TIMEOUT) = (
    60 * 10, 60 * 10, 60 * 5, 5
)

# RepoServer defaults:
_CONN_TIMEOUT = 10  # Timeout in seconds to connect to hosts w/ ssh.
_SERVER_TOPDIR = "~%(user)s/public_html/yum"  # Top dir of yum repos.
_SERVER_BASEURL = "http://%(altname)s/~%(user)s/yum"  # Base URL of yum repos.

# Repo defaults:
_SUBDIR = "%(base_name)s/%(version)s"
_BASEURL = "%(server_baseurl)s/%(dir)s"
_SIGNKEY = None
_KEYDIR = "/etc/pki/rpm-gpg"
_KEYURL = "file://%(keydir)s/RPM-GPG-KEY-%(name)s-%(version)s"

# vim:sw=4:ts=4:et:
