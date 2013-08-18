#
# Copyright (C) 2011 - 2013 Red Hat, Inc.
# Red Hat Author(s): Satoru SATOH <ssato@redhat.com>
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
import multiprocessing
import logging
import os
import os.path
import signal
import subprocess


def is_local(fqdn_or_hostname):
    """
    >>> is_local("localhost")
    True
    >>> is_local("localhost.localdomain")
    True
    >>> is_local("repo-server.example.com")
    False
    >>> is_local("127.0.0.1")  # special case:
    False
    """
    return fqdn_or_hostname.startswith("localhost")


def _validate_timeout(timeout):
    """
    Validate timeout value.

    >>> _validate_timeout(10)
    >>> _validate_timeout(0)
    >>> _validate_timeout(None)
    >>> try:
    ...     _validate_timeout(-1)
    ... except AssertionError:
    ...     pass

    :param timeout: Time value :: Int or None
    """
    assert timeout is None or int(timeout) >= 0, \
        "Invalid timeout: " + str(timeout)


def _validate_timeouts(*timeouts):
    """
    A variant of the above function to validate multiple timeout values.

    :param timeouts: List of timeout values :: [Int | None]
    """
    for to in timeouts:
        _validate_timeout(to)


def _killpg(pgid, sig=signal.SIGKILL):
    return os.killpg(pgid, sig)


def _run(cmd, workdir, rc_expected=0, logfile=False, **kwargs):
    """
    subprocess.Popen wrapper to run command ``cmd``. It will be blocked.

    An exception subprocess.CalledProcessError will be raised if
    the rc does not equal to the expected rc.

    :param cmd: Command string
    :param workdir: Working dir
    :param rc_expected: Expected return code of the command run
    :param logfile: Dump log file if True or log file path is specified
    :param kwargs: Extra keyword arguments for subprocess.Popen
    """
    assert os.path.exists(workdir), "Working dir %s does not exist!" % workdir
    assert os.path.isdir(workdir), "Working dir %s is not a dir!" % workdir

    ng_keys = ("cwd", "shell", "stdout", "stderr", "close_fds")
    kwargs = dict(((k, v) for k, v in kwargs.iteritems() if k not in ng_keys))

    rc = None
    try:
        proc = subprocess.Popen(cmd, cwd=workdir, shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                close_fds=True,
                                **kwargs)

        if logfile:
            if isinstance(logfile, bool):
                logfile = os.path.join(workdir, "%d.log" % proc.pid)

            if not os.path.exists(logfile):
                with open(logfile, 'w') as f:
                    for line in iter(proc.stdout.readline, b''):
                        f.write(line)

        if proc.wait() == rc_expected:
            return

        m = "Failed to run command: %s [%s]" % (cmd, workdir)
        raise RuntimeError(m)

    except subprocess.CalledProcessError as e:
        if rc and rc == rc_expected:
            return  # Not an error.

        raise RuntimeError(str(e))  # Raise ex again.


def _spawn(cmd, workdir, rc_expected=0, logfile=True, **kwargs):
    """
    :param cmd: Command string
    :param workdir: Working dir
    :param rc_expected: Expected return code of the command run
    :param logfile: Dump log file if True or its log file path
    :param kwargs: Extra keyword arguments for subprocess.Popen
    """
    return multiprocessing.Process(target=_run,
                                   args=(cmd, workdir, rc_expected, logfile),
                                   kwargs=kwargs)


# Connection timeout and Timeout to wait completion of runnign command in
# seconds. None or -1 means that it will wait forever.
_RUN_TO = None
_CONN_TO = 10


def init(loglevel=logging.INFO):
    multiprocessing.log_to_stderr()
    multiprocessing.get_logger().setLevel(loglevel)


def run_async(cmd, user=None, host="localhost", workdir=os.curdir,
              rc_expected=0, logfile=False, conn_timeout=_CONN_TO,
              **kwargs):
    """
    Run command ``cmd`` asyncronously.

    :param cmd: Command string
    :param user: Run command as this user
    :param host: Host on which command runs
    :param workdir: Working directory in which command runs
    :param rc_expected: Expected return code of the command run
    :param logfile: Dump log file if True or its log file path
    :param conn_timeout: Connection timeout in seconds or None

    :return: multiprocessing.Process instance
    """
    _validate_timeout(conn_timeout)

    if is_local(host):
        if "~" in workdir:
            workdir = os.path.expanduser(workdir)
    else:
        if conn_timeout is None:
            toopt = ""
        else:
            toopt = '' "-o ConnectTimeout=%d" % conn_timeout

        h = host if user is None else "%s@%s" % (user, host)

        cmd = "ssh %s %s 'cd %s && %s'" % (toopt, h, workdir, cmd)
        logging.debug("Remote host. Rewrote cmd to " + cmd)

        workdir = os.curdir

    logging.debug("Run: cmd=%s, cwd=%s" % (cmd, workdir))
    proc = _spawn(cmd, workdir, rc_expected, logfile, **kwargs)
    proc.start()

    # Hacks:
    setattr(proc, "cmd", cmd)
    setattr(proc, "cwd", workdir)

    return proc


def _force_stop_proc(proc, val0=True, val1=False):
    """
    Force stopping the given process ``proc`` and return termination was
    success or not.

    :param proc: An instance of multiprocessing.Process.
    :param val0: Return value if the process was successfully terminated.
    :param val1: Return value if the process was failed to be terminated
        and then killed.

    :return: val0 or val1 according to conditions (see above).
    """
    proc.terminate()
    if not proc.is_alive():
        return val0

    os.kill(proc.pid, signal.SIGKILL)
    return val1


def stop_async_run(proc, timeout=_RUN_TO, stop_on_error=False):
    """
    Stop the given process ``proc`` spawned from function ``run_async``.

    :param proc: An instance of multiprocessing.Process
    :param timeout: Command execution timeout in seconds or None
    :param stop_on_error: Stop and raise exception if any error occurs

    :return: True if job was sucessful else False or RuntimeError exception
        raised if stop_on_error is True
    """
    _validate_timeout(timeout)
    assert isinstance(proc, multiprocessing.Process), \
        "Invalid type of 'proc' parameter was given!"

    try:
        proc.join(timeout)

        if proc.is_alive():
            reason = _force_stop_proc(proc, "timeout", "timeout-and-killed")
        else:
            if proc.exitcode == 0:
                return True  # Exit at once w/ successful status code.

            reason = "other"

    except KeyboardInterrupt as e:
        reason = _force_stop_proc(proc, "interrupted", "interrupt-and-killed")

    m = "Failed (%s): %s" % (reason, proc.cmd)

    if stop_on_error:
        raise RuntimeError(m)

    logging.warn(m)
    return False


def run(cmd, user=None, host="localhost", workdir=os.curdir, rc_expected=0,
        logfile=False, timeout=_RUN_TO, conn_timeout=_CONN_TO,
        stop_on_error=False, **kwargs):
    """
    Run command ``cmd``.

    >>> run("true")
    True
    >>> run("false")
    False

    >>> run("sleep 10", timeout=1)
    False

    :param cmd: Command string
    :param user: User to run command
    :param host: Host to run command
    :param workdir: Working directory in which command runs
    :param rc_expected: Expected return code of the command run
    :param logfile: Dump log file if True or its log file path
    :param timeout: Command execution timeout in seconds or None
    :param conn_timeout: Connection timeout in seconds or None
    :param stop_on_error: Stop and raise exception if any error occurs

    :return: True if job was sucessful else False or RuntimeError exception
        raised if stop_on_error is True
    """
    proc = run_async(cmd, user, host, workdir, rc_expected, logfile,
                     conn_timeout, **kwargs)
    return stop_async_run(proc, timeout, stop_on_error)


def prun_async(list_of_args):
    """
    Run commands in parallel asyncronously.

    :param list_of_args: List of arguments (:: [([arg], dict(kwarg=...))]) for
        each job will be passed to ``run_async`` function.

    :return: List of multiprocessing.Process instances
    """
    return [run_async(*args, **kwargs) for args, kwargs in list_of_args]


def prun(list_of_args):
    """
    Run commands in parallel.

    :param list_of_args: List of arguments (:: [([arg], dict(kwarg=...))]) for
        each job will be passed to ``run_async`` function.

    :return: List of status of each job :: [bool]
    """
    return [run(*args, **kwargs) for args, kwargs in list_of_args]

# vim:sw=4:ts=4:et:
