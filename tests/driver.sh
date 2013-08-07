#! /bin/sh
set -ex

testsdir=${0%/*}
cd ${testsdir}/..

myrepo () {
    PYTHONPATH=. python tools/myrepo $@
}

tests=$testsdir/*.conf

for f in $tests; do
    source $f
    myrepo $MYREPO_TEST_ARGS
done
