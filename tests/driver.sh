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
    test "x$MYREPO_TEST_ARGS" = "x" || myrepo $MYREPO_TEST_ARGS
    test "x$MYREPO_TEST_ARGS_1" = "x" || myrepo $MYREPO_TEST_ARGS_1
    test "x$MYREPO_TEST_ARGS_2" = "x" || myrepo $MYREPO_TEST_ARGS_2
    test "x$MYREPO_TEST_ARGS_3" = "x" || myrepo $MYREPO_TEST_ARGS_3
done
