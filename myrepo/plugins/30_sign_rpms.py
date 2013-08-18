#
# Copyright (C) 2012 Red Hat, Inc.
# Red Hat Author(s): Satoru SATOH <ssato@redhat.com>
# License: MIT
#
try:
    import myrepo.commands as C
except:
    pass

import subprocess


_SIGN = "rpm --resign --define '_signature gpg' --define '_gpg_name %s' %s"


def sign_rpms_cmd(keyid=None, rpms=[], ask=True, fmt=_SIGN):
    """
    Make up the command string to sign RPMs.

    >>> exp = "rpm --resign --define '_signature gpg' "
    >>> exp += "--define '_gpg_name ABCD123' a.rpm b.rpm"
    >>> exp == sign_rpms_cmd("ABCD123", ["a.rpm", "b.rpm"])
    True

    TODO: It might ask user about the gpg passphrase everytime this method is
    called.  How to store the passphrase or streamline that with gpg-agent ?

    :param keyid: GPG Key ID to sign with :: str
    :param rpms: RPM file path list :: [str]
    :param ask: Ask key ID if both ``keyid`` and this are None
    """
    if keyid is None and ask:
        keyid = raw_input("Input GPG Key ID to sign RPMs > ").strip()

    return fmt % (keyid, ' '.join(rpms))


def post_build_rpms(ctx, *args, **kwargs):
    #assert "keyid" in ctx, "keyid (GPG signing key id) is missing in ctx"
    #assert "rpms_to_sign" not in ctx, \
    #    "rpms_to_sign (List of path of RPMs to sign) is missing in ctx"
    #assert ctx["rpms_to_sign"], "No RPMs to sign"

    keyid = ctx.get("keyid", False)
    rpms = ctx.get("rpms_to_sign", [])

    if keyid and rpms:
        c = sign_rpms_cmd(ignkey, rpms)
        subprocess.check_call(c, shell=True, stdin=subprocess.PIPE)


# vim:sw=4:ts=4:et:
