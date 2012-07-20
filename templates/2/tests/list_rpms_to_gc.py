#! /usr/bin/python
import glob,itertools,operator,os,os.path,rpm,sys,yum

RPM_DIR = "/var/cache/mock/fedora-17-i386/yum_cache/fedora/packages/"
RPM_KEYS = ["name", "version", "release", "epoch", "arch"]
KEEP_LIMIT = 1  # may be changed depends on 'num-deltas' in createrepo

def rpmcmp(p1, p2):
    p2evr = lambda p: (p["epoch"], p["version"], p["release"])
    return yum.compareEVR(p2evr(p1), p2evr(p2))

def file_to_p(filepath, keys=RPM_KEYS):
    h = rpm.TransactionSet("", rpm._RPMVSF_NOSIGNATURES).hdrFromFdno(open(filepath, "rb"))
    return dict(itertools.izip(["path"] + keys, [filepath] + [h[k] for k in keys]))

def rpms_group_by_names_g(rpmdir):
    ps_g = (file_to_p(f) for f in glob.glob(os.path.join(rpmdir, "*.rpm")))
    f = operator.itemgetter("name")

    for name, g in itertools.groupby(sorted(ps_g, key=f), f):
        yield sorted(list(g), cmp=rpmcmp)

def format(ps, sep="\n  "):
    return "# " + ps[0]["name"] + ":" + sep + sep.join(p["path"] for p in ps)

def main():
    rpmdir = sys.argv[1] if len(sys.argv) > 1 else RPM_DIR
    for ps in rpms_group_by_names_g(rpmdir):
        if ps and len(ps) > 1:
            print format(ps[:len(ps) - KEEP_LIMIT])

if __name__ == '__main__':
    main()
