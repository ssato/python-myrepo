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

import logging
import os
import os.path
import subprocess
import sys
import unittest


# see: http://goo.gl/7QRBR
# monkey patch to get nose working with subprocess...
def fileno_monkeypatch(self):
    return sys.__stdout__.fileno()

import StringIO
StringIO.StringIO.fileno = fileno_monkeypatch


class Test_10_run(unittest.TestCase):

    def test_00_run_async__simplest_case(self):
        proc = TT.run_async("true")
        self.assertTrue(isinstance(proc, TT.multiprocessing.Process))
        self.assertTrue(TT.stop_async_run(proc))

    def test_01_run_async__simplest_case(self):
        proc = TT.run_async("false")
        self.assertTrue(isinstance(proc, TT.multiprocessing.Process))
        self.assertFalse(TT.stop_async_run(proc))

    def test_10_run__simplest_case(self):
        self.assertTrue(TT.run("true"))
        self.assertFalse(TT.run("false"))

    def test_20_run__if_timeout(self):
        self.assertRaises(RuntimeError, TT.run,
                          "sleep 100", timeout=1, stop_on_error=True)

    def test_30_run__if_interrupted(self):
        """FIXME: How to test KeyboardInterrupt ?"""
        return

        proc = TT.run_async("sleep 5")
        raise KeyboardInterrupt("Fake Ctrl-C !")

        self.assertFalse(stop_async_run(proc))


class Test_20_prun(unittest.TestCase):

    def test_00_prun_async__simplest_case(self):
        pass

    def test_01_run_async__simplest_case(self):
        pass

    def test_10_run__simplest_case(self):
        rcs = TT.prun([(["true"], {})])
        for rc in rcs:
            self.assertTrue(rc)

# vim:sw=4 ts=4 et:
