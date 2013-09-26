#! /bin/sh
set -ex

workdir=${0%/*}

ls ${workdir}/*.src.rpm 2>/dev/null || \
rpmbuild \
  --define "_srcrpmdir ${workdir}" \
  --define "_sourcedir ${workdir}" \
  --define "_buildroot ${workdir}" -bs ${workdir}/rpm-sample.spec

