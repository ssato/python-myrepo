#! /bin/sh
set -ex

workdir=${0%/*}

rpmbuild \
  --define "_srcrpmdir ${workdir}" \
  --define "_sourcedir ${workdir}" \
  --define "_buildroot ${workdir}" -bs ${workdir}/rpm-sample.spec

