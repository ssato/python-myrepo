#
# Generate GPG key pair to sign RPMs, export GPG pub key by ID, etc.
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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
import myrepo.shell as MSH
import myrepo.utils as MU

import getpass
import logging
import os.path
import os
import re
import subprocess


_GPGKEY_COMMENT = "Custom RPM sign key"

_GPGKEY_CONF = """\
Key-Type: RSA
Key-Length: 1024
# No subkey, RSA (sign only), to keep compatibility for RHEL 5:
Key-Usage: sign
Expire-Date: 0
Name-Real: %(signer_name)s
Name-Comment: %(comment)s
Passphrase: %(passphrase)s
%%no-protection
%%transient-key
%%commit
"""

_RPMMACROS_ADD_0 = """\
%%_signature gpg
%%_gpg_name %s
"""

_RPMMACROS_ADD_1 = _RPMMACROS_ADD_0 + """
%%__gpg_sign_cmd %%{__gpg} \\
gpg --force-v3-sigs --digest-algo=sha1 --batch --no-verbose --no-armor \\
    --passphrase-fd 3 --no-secmem-warning -u "%%{_gpg_name}" \\
    -sbo %%{__signature_filename} %%{__plaintext_filename}
"""


def gen_entoropy():
    """
    Put a load on system and generate entropy needed to generate GPG key.

    FIXME: Is there any better way to generate entropy enough for GPG key
    generation ?
    """
    cmd = "find / -xdev -type f -exec sha256sum {} >/dev/null \; 2>&1"
    return MSH.run_async(cmd)


def find_keyid(signer_name, comment=_GPGKEY_COMMENT):
    """
    Find out the ID of the GPG key just created to sign RPMs.

    FIXME: Is there any other smarter way to find GPG key ID just created ?
    """
    try:
        out = subprocess.check_output("gpg --list-keys", shell=True)
        prev_line = ""
        for line in out.splitlines():
            if not line:
                continue

            if "%s %s" % (signer_name, comment) in line:
                return re.match(r"^pub +[^/]+/(\w+) .*$",
                                prev_line).groups()[0]
            prev_line = line

    except (subprocess.CalledProcessError, AttributeError):
        return None


def mk_export_gpgkey_cmd(keyid, filename, homedir_opt=''):
    """
    Export GPG key to sign RPMs.

    >>> mk_export_gpgkey_cmd("ABCDEF01", "/tmp/RPM-GPG-KEY-fedora-custom-19")
    'gpg  -a --export ABCDEF01 > /tmp/RPM-GPG-KEY-fedora-custom-19'
    """
    return "gpg %s -a --export %s > %s" % (homedir_opt, keyid, filename)


def gen_gpgkey(workdir, signer_name=None, comment=_GPGKEY_COMMENT,
               homedir=None, compat=True, passphrase=None):
    """
    Generate and configure GPG key to sign RPMs built.

    :param ctx: Context object to instantiate the template
    :param rpmmacros: .rpmmacros file path
    :param homedir: GPG's home dir (~/.gnupg by default); see also gpg(1)
    :param compat: Keep compatibility of GPG key for older RHEL if True
    :param passphrase: Passphrase for this GPG key

    :return: List of command strings to deploy built RPMs.
    """
    if signer_name is None:
        signer_name = raw_input("Signer's name: ")

    if passphrase is None:
        passphrase = getpass.getpass("Passphrase for this GPG key: ")

    homedir_opt = '' if homedir is None else "--homedir " + homedir

    gpgconf = os.path.join(workdir, ".gpg.conf")
    c = _GPGKEY_CONF % dict(signer_name=signer_name, comment=comment,
                            passphrase=passphrase)
    logging.info("Generate GPG conf to generate GPG key...")
    open(gpgconf, 'w').write(c)
    os.chmod(gpgconf, 0600)

    sproc = gen_entoropy()
    logging.info("Generate GPG key...")
    MS.run("gpg -v --batch --gen-key %s %s" % (homedir_opt, gpgconf))
    MS.stop_async_run(sproc)
    os.remove(gpgconf)

    keyid = find_keyid(signer_name, comment)

    logging.info("Generated GPG key ID=" + keyid)
    return keyid


def tweak_rpm_macros(keyid):
    rpmmacros = os.path.expanduser("~/.rpmmacros")

    if os.path.exists(rpmmacros):
        m = "~/.rpmmacros already exists! Edit it manually as needed."
        logging.warn(m)
    else:
        fmt = _RPMMACROS_ADD_1 if compat else _RPMMACROS_ADD_0
        open(rpmmacros, 'w').write(fmt % dict(keyid=keyid, ))
        logging.info("Added GPG key configurations to " + rpmmacros)


# vim:sw=4:ts=4:et:
