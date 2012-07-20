#
# Copyright (C) 2012 Red Hat, Inc.
# Red Hat Author(s): Satoru SATOH <ssato@redhat.com>
# License: MIT
#
import myrepo.repoops as RO
import subprocess


def post_build_rpms(repo, *args, **kwargs):
    if repo.signkey:
        c = RO.sign_rpms_cmd(repo.signkey, repo.rpms_to_sign)
        subprocess.check_call(c, shell=True)


# vim:sw=4:ts=4:et:
