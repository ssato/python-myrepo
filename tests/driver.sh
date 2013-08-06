#! /bin/sh
set -ex

testsdir=${0%/*}
cd ${testsdir}/..

run () {
    PYTHONPATH=. python tools/myrepo $@
}

tests=$testsdir/*.conf

for f in $tests; do
    source $f
    run $MYREPO_TEST_ARGS
done
