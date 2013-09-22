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
import myrepo.commands.init
import myrepo.commands.genconf
import myrepo.commands.build
import myrepo.commands.deploy
import myrepo.commands.update


# command_abrev, command, help, mod_function
LIST = [('i', "init", "Initialize yum repo", myrepo.commands.init.run),
        ('genc', "genconf",
         "Generate .repo and mock.cfg RPMs for yum repos",
         myrepo.commands.genconf),
        ('u', "update", "Update the meta data of yum repos",
         myrepo.commands.update),
        ('b', "build", "Build given SRPMs for the yum repos",
         myrepo.commands.build),
        ('d', "deploy",
         "Build and deploy given SRPMs for the yum repos",
         myrepo.commands.deploy)]

# vim:sw=4:ts=4:et:
