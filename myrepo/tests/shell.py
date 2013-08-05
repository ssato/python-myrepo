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

import logging
import os
import os.path
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


class Test_10_run(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_00_run_async__simplest_case(self):
        logfile = os.path.join(self.workdir, "true.log")
        proc = TT.run_async("true", workdir=self.workdir, logfile=logfile)

        self.assertTrue(isinstance(proc, TT.multiprocessing.Process))
        self.assertTrue(TT.stop_async_run(proc))
        self.assertTrue(os.path.exists(logfile))

    def test_01_run_async__simplest_case(self):
        proc = TT.run_async("false", workdir=self.workdir, logfile=True)
        self.assertTrue(isinstance(proc, TT.multiprocessing.Process))
        self.assertFalse(TT.stop_async_run(proc))

    def test_10_run__simplest_case(self):
        self.assertTrue(TT.run("true", workdir=self.workdir, logfile=True))
        self.assertFalse(TT.run("false", workdir=self.workdir, logfile=True))

    def test_20_run__if_timeout(self):
        self.assertRaises(RuntimeError, TT.run,
                          "sleep 100", workdir=self.workdir, logfile=True,
                          timeout=1, stop_on_error=True)

    def test_30_run__if_interrupted(self):
        proc = TT.run_async("sleep 20", workdir=self.workdir, logfile=True)
        interrupter = TT.run_async("sleep 3 && kill -s INT %d" % proc.pid,
                                   logfile=False)

        self.assertFalse(TT.stop_async_run(proc))


class Test_20_prun(unittest.TestCase):

    def setUp(self):
        self.workdir = C.setup_workdir()

    def tearDown(self):
        C.cleanup_workdir(self.workdir)

    def test_00_prun_async__simplest_case(self):
        pass

    def test_01_run_async__simplest_case(self):
        pass

    def test_10_run__simplest_case(self):
        rcs = TT.prun([(["true"], dict(workdir=self.workdir))])
        for rc in rcs:
            self.assertTrue(rc)

# vim:sw=4 ts=4 et:
