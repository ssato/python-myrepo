#
# Copyright (C) 2012 Red Hat, Inc.
# Red Hat Author(s): Satoru SATOH <ssato@redhat.com>
# License: MIT
#
import myrepo.commands as C
import subprocess


def post_build_rpms(ctx, *args, **kwargs):
    if repo.signkey:
        c = C.sign_rpms_cmd(ctx["repo"].signkey, ctx["rpms_to_sign"])
        subprocess.check_call(c, shell=True)


# vim:sw=4:ts=4:et:
