#! /bin/sh
set -ex

testsdir=${0%/*}
cd ${testsdir}/..

myrepo () {
    PYTHONPATH=. python tools/myrepo $@
}

test $# -gt 0 && tests=$@ || tests=$testsdir/*.conf

# default impl (do nothing):
check_func () { true; }
check_func_1 () { true; }
check_func_2 () { true; }
check_func_3 () { true; }

for f in $tests; do
    source $f
    test "x$MYREPO_TEST_ARGS" = "x" || (myrepo $MYREPO_TEST_ARGS && check_func)
    test "x$MYREPO_TEST_ARGS_1" = "x" || (myrepo $MYREPO_TEST_ARGS_1 && check_func_1)
    test "x$MYREPO_TEST_ARGS_2" = "x" || (myrepo $MYREPO_TEST_ARGS_2 && check_func_2)
    test "x$MYREPO_TEST_ARGS_3" = "x" || (myrepo $MYREPO_TEST_ARGS_3 && check_func_3)
done
