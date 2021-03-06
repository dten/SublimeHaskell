"""
Miscelaneous glue, mostly for interoperability between Python2 and Python3.
"""

import os
import os.path
import platform
import queue
import threading
import traceback

import SublimeHaskell.internals.logging as Logging

def decode_bytes(src):
    return src.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n') if src is not None else None


def encode_bytes(src):
    return src.replace('\r\n', os.linesep).replace('\n', os.linesep).encode('utf-8') if src is not None else None


def head_of(lst):
    return lst[0] if lst is not None and len(lst) > 0 else None


def tool_enabled(feature):
    """Generate the name of a feature to test whether it is enabled."""
    return 'enable_' + str(feature)

def normalize_path(dpath):
    return os.path.normpath(os.path.expandvars(os.path.expanduser(dpath)))

def is_windows():
    return platform.system() == "Windows"

class Singleton(type):
    '''Singleton meta-class. This ensures that only one instance of an object is every alive at any given time during
    program execution. Principally used in backends and backend management, where only one NullHaskellBackend and
    one BackendManager class and instance ever need to be alive.
    '''
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

# Background worker
class Worker(object, metaclass=Singleton):
    def __init__(self):
        super().__init__()
        self.jobs = queue.Queue()
        self.inner_thread = threading.Thread(target=self.worker_run)
        self.inner_thread.start()

    def worker_run(self):
        while True:
            name, worker_fn, args, kwargs = self.jobs.get()
            try:
                Logging.log('worker: {0}'.format(name), Logging.LOG_DEBUG)
                worker_fn(*args, **kwargs)
            except Exception:
                Logging.log('worker: job {0} failed, see console window traceback'.format(name), Logging.LOG_ERROR)
                traceback.print_exc()

    def async(self, name, worker_fn, *args, **kwargs):
        self.jobs.put((name, worker_fn, args, kwargs))

def run_async(name, worker_fn, *args, **kwargs):
    Worker().async(name, worker_fn, *args, **kwargs)
