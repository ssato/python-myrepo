#
# Copyright (C) 2013 Red Hat, Inc.
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
import rpmkit.rpmutils as RU


class Srpm(object):

    def __init__(self, path):
        self.path = path

        self.name = None
        self.version = None
        self.release = None
        self.noarch = None

        self.is_srpm = None
        self.resolved = False

    def resolve(self):
        try:
            h = RU.rpm_header_from_rpmfile(self.path)

            self.is_srpm = bool(h["sourcepackage"])
            self.noarch = h["arch"] == "noarch"

            for k in ("name", "version", "release"):
                setattr(self, k, h[k])

            self.resolved = True
        except:
            raise RuntimeError("Failed to get rpm header from: " + self.path)


# vim:sw=4:ts=4:et:
