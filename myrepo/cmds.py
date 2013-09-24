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
_LIST = [('i', "init", "Initialize yum repo", myrepo.commands.init.run),
         ('genc', "genconf",
          "Generate .repo and mock.cfg RPMs for yum repos",
          myrepo.commands.genconf.run),
         ('u', "update", "Update the meta data of yum repos",
          myrepo.commands.update.run),
         ('b', "build", "Build given SRPMs for the yum repos",
          myrepo.commands.build.run),
         ('d', "deploy",
          "Build and deploy given SRPMs for the yum repos",
          myrepo.commands.deploy.run)]


class CommandNotFoundError(Exception):
    pass


def mk_cmd_helps_text(cmds=_LIST):
    def f():
        for abbrev, cmd_s, help, func in cmds:
            yield "  %s\t%s" % (cmd_s.replace(abbrev, "[%s]" % abbrev, 1),
                                help)

    return "\nComands:\n" + '\n'.join(s for s in f())


def find_cmd(subcmd_s, cmds=_LIST):
    """
    Find command function corresponding to args.

    :param subcmd_s: A string represents sub command or its abbrev.
    :return: Command implementation (callable object)

    >>> find_cmd("ini") == myrepo.commands.init.run
    True
    >>> find_cmd("i") == myrepo.commands.init.run
    True
    >>> find_cmd("u") == myrepo.commands.update.run
    True
    >>> find_cmd("xyz")  # +ELLIPSIS
    Traceback (most recent call last):
    CommandNotFoundError: No match for the sub command or abbrev: xyz
    """
    for abbrev, _cmd_s, _help, func in cmds:
        if subcmd_s.startswith(abbrev):
            return func

    m = "No match for the sub command or abbrev: " + subcmd_s
    raise CommandNotFoundError(m)


# vim:sw=4:ts=4:et:
