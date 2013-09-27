#
# Copyright (C) 2012, 2013 Satoru SATOH <satoru.satoh @ gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import myrepo.shell as TT
import myrepo.tests.common as C

import itertools
import logging
import os.path
import os
import signal
import sys
import unittest


# see: http://goo.gl/7QRBR
# monkey patch to get nose working with subprocess...
def fileno_monkeypatch(self):
    return sys.__stdout__.fileno()

import StringIO
StringIO.StringIO.fileno = fileno_monkeypatch


def delayed_interrupt(pid, wait=10):
    os.sleep(wait)

    p = TT.multiprocessing.Process(target=os.kill,
                                   args=(pid, signal.SIGINT))
    p.start()
    p.join()

    if p.is_alive():
        p.terminate()


class Test_00_functions(unittest.TestCase):

    def test_10_local__fullpath_workdir(self):
        (cmd, workdir) = TT.adjust_cmd("true", workdir="/tmp")

        self.assertEquals(cmd, "cd /tmp && true")
        self.assertEquals(workdir, ".")

    def test_12_local__user_workdir(self):
        """TODO: How to test cases if "~" in workdir"""
        pass

    def test_14_remote__no_conn_timeout(self):
        (cmd, workdir) = TT.adjust_cmd("true", host="repos.example.com",
                                       workdir="/tmp", conn_timeout=None)
        self.assertEquals(cmd, "ssh  repos.example.com 'cd /tmp && true'")
        self.assertEquals(workdir, os.curdir)

    def test_16_remote__no_conn_timeout(self):
        (cmd, workdir) = TT.adjust_cmd("true", host="repos.example.com",
                                       workdir="/tmp", conn_timeout=7)
        cmdref = "ssh -o ConnectTimeout=7 repos.example.com 'cd /tmp && true'"

        self.assertEquals(cmd, cmdref)
        self.assertEquals(workdir, os.curdir)


class Test_10_run(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()
        self.logfile = os.path.join(self.workdir, "%d.log" % os.getpid())
        self.kwargs = dict(workdir=self.workdir, logfile=self.logfile)

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_00_run_async__simplest_case(self):
        proc = TT.run_async("true", **self.kwargs)

        self.assertTrue(isinstance(proc, TT.multiprocessing.Process))
        self.assertTrue(TT.stop_async_run(proc))
        self.assertTrue(os.path.exists(self.logfile))

    def test_01_run_async__simplest_case(self):
        proc = TT.run_async("false", **self.kwargs)

        self.assertTrue(isinstance(proc, TT.multiprocessing.Process))
        self.assertFalse(TT.stop_async_run(proc))
        self.assertTrue(os.path.exists(self.logfile))

    def test_02_run_async__simplest_case(self):
        proc = TT.run_async("sleep 5 && true", **self.kwargs)

        self.assertTrue(isinstance(proc, TT.multiprocessing.Process))
        self.assertFalse(TT.stop_async_run(proc, 2))
        self.assertTrue(os.path.exists(self.logfile))

    def test_04_run_async__simplest_case_w_callable_logfile(self):
        def logfile():
            return os.path.join(self.workdir, "dynamic_logfile.log")

        kwargs = self.kwargs
        logfile_path = logfile()
        kwargs["logfile"] = logfile  # It's callable object.

        proc = TT.run_async("sleep 5 && true", **kwargs)

        self.assertTrue(isinstance(proc, TT.multiprocessing.Process))
        self.assertFalse(TT.stop_async_run(proc, 2))
        self.assertTrue(os.path.exists(logfile_path))

    def test_10_run__simplest_case(self):
        self.assertTrue(TT.run("true", **self.kwargs))
        self.assertFalse(TT.run("false", **self.kwargs))
        self.assertTrue(os.path.exists(self.logfile))

    def test_20_run__if_timeout(self):
        self.assertRaises(RuntimeError, TT.run,
                          "sleep 100", workdir=self.workdir,
                          logfile=self.logfile, timeout=1, stop_on_error=True)

    def test_30_run__if_interrupted(self):
        proc = TT.run_async("sleep 20", **self.kwargs)
        interrupter = TT.run_async("sleep 3 && kill -s INT %d" % proc.pid,
                                   **self.kwargs)

        self.assertFalse(TT.stop_async_run(proc))

    def test_50_prun_async__simplest_case(self):
        cntr = itertools.count()
        logfile = lambda: os.path.join(self.workdir,
                                       "%d.%d.log" % (os.getpid(),
                                                      cntr.next()))

        ps = TT.prun_async(["sleep 5 && true" for _ in range(5)],
                           workdir=self.workdir, logfile=logfile())

        for proc in ps:
            self.assertTrue(isinstance(proc, TT.multiprocessing.Process))
            #self.assertFalse(TT.stop_async_run(proc, 2))

        #self.assertTrue(os.path.exists(self.logfile))


# vim:sw=4 ts=4 et:
