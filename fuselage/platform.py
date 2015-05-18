# Copyright 2011-2014 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import errno
import subprocess
import os
import select
import sys
import threading

import six

try:
    import pwd
except ImportError:  # pragma: no cover
    pwd = None
try:
    import grp
except ImportError:  # pragma: no cover
    grp = None
try:
    import spwd
except ImportError:  # pragma: no cover
    spwd = None


from fuselage import error
from fuselage.utils import force_str, force_bytes


platform = sys.platform
pathsep = os.pathsep


class Handle(object):

    def __init__(self, handle, callback=None):
        self.handle = handle
        self.callback = callback
        self._output = []

    def fileno(self):
        return self.handle.fileno()

    def read(self):
        data = os.read(self.fileno(), 1024)
        if not data:
            self.handle.close()
            return False
        self.feed(data)

    def read_win32(self):
        self.feed(self.handle.read())

    def feed(self, data):
        data = force_str(data)

        self._output.append(data)

        if self.callback:
            for l in data.splitlines():
                self.callback(l)

        return True

    def isready(self):
        return bool(self.handle)

    @property
    def output(self):
        out = ''.join(self._output)
        return out


class Process(subprocess.Popen):

    def __init__(self, command, user=None, uid=None, gid=None, group=None, umask=None, **kwargs):
        self.callback = None
        self.uid = uid
        self.gid = gid
        if user and pwd:
            self.uid = pwd.getpwnam(user).pw_uid
        if group and grp:
            self.gid = grp.getgrnam(group).gr_gid
        self.umask = umask

        if platform != 'win32':
            kwargs['preexec_fn'] = self.preexec
        if 'stdout' not in kwargs:
            kwargs['stdout'] = subprocess.PIPE
        if 'stderr' not in kwargs:
            kwargs['stderr'] = subprocess.PIPE
        super(Process, self).__init__(command, **kwargs)

    def preexec(self):
        if self.gid:
            if self.gid != os.getgid():
                os.setgid(self.gid)
            if self.gid != os.getegid():
                os.setegid(self.gid)

        if self.uid:
            if self.uid != os.getuid():
                os.setuid(self.uid)
            if self.uid != os.geteuid():
                os.seteuid(self.uid)

        if self.umask:
            os.umask(self.umask)

    def attach_callback(self, callback):
        self.callback = callback

    def communicate_win32(self, stdout, stderr):
        if self.stdout:
            stdout_thread = threading.Thread(
                target=stdout.read_win32,
            )
            stdout_thread.setDaemon(True)
            stdout_thread.start()

        if self.stderr:
            stderr_thread = threading.Thread(
                target=stderr.read_win32,
            )
            stderr_thread.setDaemon(True)
            stderr_thread.start()

        if self.stdout:
            stdout_thread.join()

        if self.stderr:
            stderr_thread.join()

        self.wait()

    def communicate_posix(self, stdout, stderr):
        # Initial readlist is any handle that is valid
        readlist = [h for h in (stdout, stderr) if h.isready()]

        while readlist:
            try:
                # Wait for data on stdout or stderr handles, but timeout after
                # one second so that we can poll (below) and check the process
                # hasn't disappeared.
                rlist, wlist, xlist = select.select(readlist, [], [], 1)
            except select.error as e:
                if e.args[0] == errno.EINTR:
                    continue
                raise

            # Some processes hang if we don't specifically poll for them going
            # away. We believe that under certain cases, child processes can
            # reuse their parent's file descriptors, and in that case, the
            # select loop will continue until the child process goes away, which
            # is undesirable when starting a daemon process.
            if not rlist and not wlist and not xlist:
                if self.poll() is not None:
                    break

            # Read from all handles that select told us can be read from
            # If they return false then we are at the end of the stream
            # and stop reading from them
            for r in rlist:
                if not r.read():
                    readlist.remove(r)

    def communicate(self, input=None):
        stdout = Handle(self.stdout, self.callback)
        stderr = Handle(self.stderr, self.callback)

        if self.stdin:
            if input is not None:
                try:
                    self.stdin.write(input)
                except IOError as e:
                    if e.errno != errno.EPIPE:
                        raise
                self.stdin.flush()
            self.stdin.close()

        if platform == "win32":
            self.communicate_win32(stdout, stderr)
        else:
            self.communicate_posix(stdout, stderr)

        return stdout.output, stderr.output


def check_call(command, *args, **kwargs):
    logger = kwargs.pop('logger', None)
    expected = kwargs.pop('expected', 0)
    encoding = kwargs.pop('encoding', 'UTF-8')
    stdin = kwargs.pop('stdin', None)
    kwargs['stdin'] = subprocess.PIPE if stdin else None
    kwargs.setdefault('shell', not isinstance(command, list))

    env = {}
    if platform == "posix":
        env.update({"PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"})
    env.update(kwargs.get("env", {}))
    kwargs['env'] = env

    p = Process(command, *args, **kwargs)
    if logger:
        p.attach_callback(logger.info)
    stdout, stderr = p.communicate(input=stdin)
    p.wait()
    if encoding and not isinstance(stdout, six.text_type):
        stdout = stdout.decode(encoding)
    if encoding and not isinstance(stderr, six.text_type):
        stderr = stderr.decode(encoding)
    if expected is not None and p.returncode != expected:
        raise error.SystemError(p.returncode, stdout, stderr)
    return stdout, stderr


def exists(path):
    return os.path.exists(path)


def isfile(path):
    return os.path.isfile(path)


def isdir(path):
    return os.path.isdir(path)


def islink(path):
    return os.path.islink(path)


def stat(path):
    return os.stat(path)


def lexists(path):
    return os.path.lexists(path)


def readlink(path):
    return os.readlink(path)


def lstat(path):
    return os.lstat(path)


def get(path):
    return open(path).read()


def put(path, contents, chmod=0o644):
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if not sys.platform.startswith("win"):
        flags = flags | os.O_SYNC
    fd = os.open(path, flags, chmod)
    try:
        os.write(fd, force_bytes(contents))
    finally:
        os.close(fd)


def makedirs(path):
    os.makedirs(path)


def unlink(path):
    os.unlink(path)


def gr_supported():
    return grp is not None


def pwd_supported():
    return pwd is not None


def spwd_supported():
    return spwd is not None

if gr_supported():
    def getgrall():
        return list(grp.getgrall())

    def getgrnam(name):
        return grp.getgrnam(name)

    def getgrgid(gid):
        return grp.getgrgid(gid)
else:
    getgrall = None
    getgrnam = None
    getgrgid = None


if pwd_supported():
    def getpwall():
        return list(pwd.getpwall())

    def getpwnam(name):
        return pwd.getpwnam(name)

    def getpwuid(uid):
        return pwd.getpwuid(uid)
else:
    getpwall = None
    getpwnam = None
    getpwuid = None


if spwd_supported():
    def getspall():
        return list(spwd.getspall())

    def getspnam(name):
        return spwd.getspnam(name)
else:
    getspall = None
    getspnam = None


def getuid():
    return os.getuid()
