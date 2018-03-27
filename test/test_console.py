import sys
from code import InteractiveInterpreter
import socket

from threading import local

_local = local()
_displayhook = sys.displayhook


class StringO(object):

    """A StringO version that HTML escapes on write."""

    def __init__(self):
        self._buffer = []

    def isatty(self):
        return False

    def close(self):
        pass

    def flush(self):
        pass

    def seek(self, n, mode=0):
        pass

    def readline(self):
        if len(self._buffer) == 0:
            return ''
        ret = self._buffer[0]
        del self._buffer[0]
        return ret

    def reset(self):
        val = ''.join(self._buffer)
        del self._buffer[:]
        return val

    def _write(self, x):
        if isinstance(x, bytes):
            x = x.decode('utf-8', 'replace')
        self._buffer.append(str(x))

    def write(self, x):
        self._write(x)

    def writelines(self, x):
        self._write(''.join(x))


class ThreadedStream(object):

    """Thread-local wrapper for sys.stdout for the interactive console."""

    def push():
        if not isinstance(sys.stdout, ThreadedStream):
            sys.stdout = ThreadedStream()
        _local.stream = StringO()
    push = staticmethod(push)

    def fetch():
        try:
            stream = _local.stream
        except AttributeError:
            return ''
        return stream.reset()
    fetch = staticmethod(fetch)

    def displayhook(obj):
        try:
            stream = _local.stream
        except AttributeError:
            return _displayhook(obj)
        # stream._write bypasses escaping as debug_repr is
        # already generating HTML for us.
        if obj is not None:
            _local._current_ipy.locals['_'] = obj
            stream._write(obj)
    displayhook = staticmethod(displayhook)

    def __setattr__(self, name, value):
        raise AttributeError('read only attribute %s' % name)

    def __dir__(self):
        return dir(sys.__stdout__)

    def __getattribute__(self, name):
        if name == '__members__':
            return dir(sys.__stdout__)
        try:
            stream = _local.stream
        except AttributeError:
            stream = sys.__stdout__
        return getattr(stream, name)

    def __repr__(self):
        return repr(sys.__stdout__)


sys.displayhook = ThreadedStream.displayhook


class CustomInteractiveInterpreter(InteractiveInterpreter):

    def __init__(self, locals):
        super(CustomInteractiveInterpreter, self).__init__(locals)
        self.buffer = []
        self.stdout = sys.stdout

    def stop(self):
        sys.stdout = self.stdout

    def runsource(self, source):
        source = source.rstrip() + '\n'
        try:
            ThreadedStream.push()
            source_to_eval = ''.join(self.buffer + [source])
            if super(CustomInteractiveInterpreter, self).runsource(source_to_eval, '<debugger>', 'single'):
                self.buffer.append(source)
            else:
                del self.buffer[:]
        finally:
            output = ThreadedStream.fetch()
            self.stop()
        return output

    def write(self, data):
        sys.stdout.write(data)

ii = CustomInteractiveInterpreter()

_local._current_ipy = ii


def main():

    server = socket.socket()
    server.bind(("", 1234))
    server.listen(0)
    client, addr = server.accept()
    print("recv from %s:%s. "%addr)
    cmd = client.recv(1024)
    client.send(ii.runsource(cmd.decode()).encode())
    client.close()
    server.close()

main()
