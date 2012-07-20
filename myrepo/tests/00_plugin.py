import sys

A = 0


def __log_info(fn, *args, **kwargs):
    print >> sys.stderr, "called %s w/ args=%s, kwargs=%s" % \
        (fn, str(args), str(kwargs))


def pre_init(*args, **kwargs):
    __log_info("pre_init", *args, **kwargs)


def post_init(*args, **kwargs):
    __log_info("post_init", *args, **kwargs)

# vim:sw=4:ts=4:et:
