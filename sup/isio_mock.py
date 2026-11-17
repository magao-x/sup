"""A stand-in for ImageStreamIOWrap, the Python binding to milk's shared
memory image streams, for working on sup where the real module can't be
built: it leans on Linux-only semaphore calls, so not on macOS.

It mirrors the binding's API surface (names, signatures, return codes, the
exceptions it raises, column-major array layout) rather than its
implementation, so code written against this runs unchanged against the
real thing::

    try:
        import ImageStreamIOWrap as ISIO
    except ImportError:
        from sup import isio_mock as ISIO

Images are still shared between processes, so a fake camera in one process
can feed sup in another. Each is a memory-mapped file in the directory the
real library would use (``$MILK_SHM_DIR``, else ``/milk/shm``, else
``/tmp``), named ``<name>.im.mock`` rather than ``<name>.im.shm`` so neither
library ever mistakes the other's files for its own. Semaphores are counters
in that file guarded by ``flock``, and waiting on one polls it, since macOS
also lacks ``sem_timedwait`` and ``sem_getvalue``. A listener looks the same
as with the real binding::

    img = ISIO.Image()
    img.open("camwfs")
    index = img.getsemwaitindex(0)
    img.semflush(index)
    while True:
        img.semwait(index)
        frame = img.copy()

That loop belongs on a main thread with nothing else to do. The binding
holds the GIL while it waits, so on Linux a blocking wait in a worker thread
stalls every thread, and in an event loop it stalls the loop. Waiting here
sleeps between looks, which would hide that, so instead a blocking wait from
either place raises a BlockingWaitWarning.

Not mocked: GPU images, circular buffers, process traces, and the per-slice
time and counter arrays.
"""
import asyncio
import contextlib
import datetime
import enum
import fcntl
import mmap
import numbers
import os
import tempfile
import threading
import time
import warnings

import numpy as np

SHAREDMEMDIR = "/milk/shm"
FILE_SUFFIX = ".im.mock"
IMAGESTRUCT_VERSION = "2.00"
KEYWORD_MAX_STRING = 16
KEYWORD_MAX_COMMENT = 80
SEMAPHORE_MAXVAL = 10
IMAGE_NB_SEMAPHORE = 10

IMAGESTREAMIO_SUCCESS = 0
IMAGESTREAMIO_INVALIDARG = 10
IMAGESTREAMIO_FILEOPEN = 40
# What the semaphore calls return for an index out of range, alongside the
# 0 / -1 they pass through from sem_wait() and friends.
EXIT_FAILURE = 1

_MAGIC = b"ISIOMOCK"
_LAYOUT_VERSION = 1
_DATA_ALIGNMENT = 64
_MATH_DATA = 0x0002
# Bounds on how long a waiter sleeps between looks at its semaphore.
_POLL_MIN_SEC = 0.0002
_POLL_MAX_SEC = 0.002


class BlockingWaitWarning(RuntimeWarning):
    """A wait that would block more than its own thread under the real binding."""


def _warn_if_wait_blocks_others(call):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        if threading.current_thread() is threading.main_thread():
            return
        where = "off the main thread, where the real binding would stall every thread"
    else:
        where = "inside a running event loop, which the real binding would stall"
    warnings.warn(
        f"{call}() called {where}, since it holds the GIL while waiting; "
        "poll md.cnt0 or semtrywait() instead",
        BlockingWaitWarning,
        stacklevel=3,
    )


def _enum_or_int(enum_cls, value):
    try:
        return enum_cls(value)
    except ValueError:
        return value


class ImageStreamIODataType:
    class Type(enum.IntEnum):
        UINT8 = 1
        INT8 = 2
        UINT16 = 3
        INT16 = 4
        UINT32 = 5
        INT32 = 6
        UINT64 = 7
        INT64 = 8
        FLOAT = 9
        DOUBLE = 10
        COMPLEX_FLOAT = 11
        COMPLEX_DOUBLE = 12
        HALF = 13

    _SIZES = (0, 1, 1, 2, 2, 4, 4, 8, 8, 4, 8, 8, 16, 2)

    def __init__(self, datatype):
        if not 1 <= datatype < len(self._SIZES):
            raise ValueError(f"invalid datatype code {datatype}")
        self._type = self.Type(datatype)

    @property
    def type(self):
        return self._type

    @property
    def size(self):
        return self._SIZES[self._type]

    def __repr__(self):
        return f"datatype: {int(self._type)}\nsize: {self.size}\n"


class ImageStreamIOType:
    class Type(enum.IntEnum):
        CIRCULAR_BUFFER_TYPE = 0x0001
        MATH_DATA_TYPE = 0x0002
        IMG_RECV_TYPE = 0x0004
        IMG_SENT_TYPE = 0x0008
        ZAXIS_UNDEF_TYPE = 0x00000
        ZAXIS_SPACIAL_TYPE = 0x10000
        ZAXIS_TEMPORAL_TYPE = 0x20000
        ZAXIS_WAVELENGTH_TYPE = 0x30000
        ZAXIS_MAPPING_TYPE = 0x40000

    def __init__(self, type):
        self._value = int(type)

    @property
    def type(self):
        return _enum_or_int(self.Type, self._value & 0xF)

    @property
    def axis(self):
        return _enum_or_int(self.Type, self._value & 0xF0000)

    def __repr__(self):
        return f"type: {int(self.type)}\naxis: {int(self.axis)}\n"


# The binding exports its enum values onto the enclosing class too, as in
# ImageStreamIODataType.FLOAT.
for _cls in (ImageStreamIODataType, ImageStreamIOType):
    for _member in _cls.Type:
        setattr(_cls, _member.name, _member)

# The datatypes the binding can move in and out of numpy; it has no buffer
# format for half precision or complex numbers.
_NUMPY_DTYPES = {
    ImageStreamIODataType.UINT8: np.dtype(np.uint8),
    ImageStreamIODataType.INT8: np.dtype(np.int8),
    ImageStreamIODataType.UINT16: np.dtype(np.uint16),
    ImageStreamIODataType.INT16: np.dtype(np.int16),
    ImageStreamIODataType.UINT32: np.dtype(np.uint32),
    ImageStreamIODataType.INT32: np.dtype(np.int32),
    ImageStreamIODataType.UINT64: np.dtype(np.uint64),
    ImageStreamIODataType.INT64: np.dtype(np.int64),
    ImageStreamIODataType.FLOAT: np.dtype(np.float32),
    ImageStreamIODataType.DOUBLE: np.dtype(np.float64),
}


def _datatype_of(dtype):
    for code, candidate in _NUMPY_DTYPES.items():
        if dtype == candidate:
            return code
    return None


_HEADER = np.dtype([
    ("magic", "S8"),
    ("layout", "<u4"),
    ("version", "S32"),
    ("name", "S80"),
    ("naxis", "u1"),
    ("datatype", "u1"),
    ("shared", "u1"),
    ("location", "i1"),
    ("logflag", "u1"),
    ("write", "u1"),
    ("size", "<u4", (3,)),
    ("nelement", "<u8"),
    ("imagetype", "<u8"),
    ("creationtime", "<i8"),
    ("lastaccesstime", "<i8"),
    ("acqtime", "<i8"),
    ("writetime", "<i8"),
    ("status", "<i4"),
    ("sem", "<i4"),
    ("NBkw", "<i4"),
    ("inode", "<u8"),
    ("cnt0", "<u8"),
    ("cnt1", "<u8"),
    ("cnt2", "<u8"),
    ("flag", "<u8"),
], align=True)

# The real IMAGE_KEYWORD keeps its value in a union; here each kind gets a field.
_KEYWORD = np.dtype([
    ("name", f"S{KEYWORD_MAX_STRING}"),
    ("type", "S1"),
    ("numl", "<i8"),
    ("numf", "<f8"),
    ("valstr", f"S{KEYWORD_MAX_STRING}"),
    ("comment", f"S{KEYWORD_MAX_COMMENT}"),
])


class _Layout:
    """Byte offsets of each region: header, semaphore values, reader PIDs,
    writer PIDs, keywords, then the pixels."""
    def __init__(self, nsem, nkw, nbytes):
        self.semval = _HEADER.itemsize
        self.sem_read_pid = self.semval + 4 * nsem
        self.sem_write_pid = self.sem_read_pid + 4 * nsem
        self.kw = self.sem_write_pid + 4 * nsem
        kw_end = self.kw + _KEYWORD.itemsize * nkw
        self.data = -(-kw_end // _DATA_ALIGNMENT) * _DATA_ALIGNMENT
        self.total = self.data + nbytes


class _BadFile(Exception):
    pass


def _shmdirname():
    env = os.environ.get("MILK_SHM_DIR")
    if env is not None:
        if os.path.isdir(env):
            return env
        print(f" [ WARNING ] '{env}' does not exist")
    if os.path.isdir(SHAREDMEMDIR):
        return SHAREDMEMDIR
    return "/tmp"


def _filename(name):
    return os.path.join(_shmdirname(), name + FILE_SUFFIX)


def _decode(raw):
    return raw.decode("utf-8", "replace")


def _datetime(ns):
    # pybind11 hands system_clock time points to Python as naive local times.
    ns = int(ns)
    return (datetime.datetime.fromtimestamp(ns // 10**9)
            + datetime.timedelta(microseconds=(ns % 10**9) // 1000))


def _pid_alive(pid):
    try:
        os.getpgid(pid)
    except ProcessLookupError:
        return False
    return True


_UNSET = object()


class Image_kw:
    def __init__(self, name=_UNSET, value=_UNSET, comment="", *,
                 numl=_UNSET, numf=_UNSET, valstr=_UNSET):
        self._name, self._type, self._value, self._comment = "", "\x00", None, ""
        given = [(kind, v) for kind, v in
                 ((None, value), ("L", numl), ("D", numf), ("S", valstr))
                 if v is not _UNSET]
        if name is _UNSET and not given:
            return
        if name is _UNSET or len(given) != 1:
            raise TypeError("Image_kw(): incompatible constructor arguments")
        kind, value = given[0]
        if isinstance(value, str):
            inferred = "S"
        elif isinstance(value, numbers.Integral):
            inferred = "L"
        elif isinstance(value, numbers.Real):
            inferred = "D"
        else:
            raise TypeError("Image_kw(): incompatible constructor arguments")
        # An int is fine where a double is asked for, but nothing else converts.
        if kind is not None and kind != inferred and not (kind == "D" and inferred == "L"):
            raise TypeError("Image_kw(): incompatible constructor arguments")
        kind = kind or inferred
        if len(name.encode()) > KEYWORD_MAX_STRING:
            raise ValueError("name too long")
        if kind == "S" and len(value.encode()) > KEYWORD_MAX_STRING:
            raise ValueError("valstr too long")
        if len(comment.encode()) > KEYWORD_MAX_COMMENT:
            raise ValueError("comment too long")
        self._name, self._type, self._comment = name, kind, comment
        self._value = {"L": int, "D": float, "S": str}[kind](value)

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @property
    def value(self):
        if self._type not in ("L", "D", "S"):
            raise RuntimeError("Unknown format")
        return self._value

    @property
    def comment(self):
        return self._comment

    def __str__(self):
        if self._type == "L":
            text = str(self._value)
        elif self._type == "D":
            # C++ streams print doubles with six significant digits.
            text = format(self._value, ".6g")
        elif self._type == "S":
            text = self._value
        else:
            text = "Unknown format"
        return f"{text} {self._comment}"

    __repr__ = __str__

    def _to_record(self, record):
        record["name"] = self._name.encode()
        record["type"] = self._type.encode()
        record["numl"] = self._value if self._type == "L" else 0
        record["numf"] = self._value if self._type == "D" else 0.0
        record["valstr"] = self._value.encode() if self._type == "S" else b""
        record["comment"] = self._comment.encode()

    @classmethod
    def _from_record(cls, record):
        kw = cls()
        kw._name = _decode(record["name"])
        kw._type = _decode(record["type"]) or "\x00"
        kw._comment = _decode(record["comment"])
        if kw._type == "L":
            kw._value = int(record["numl"])
        elif kw._type == "D":
            kw._value = float(record["numf"])
        elif kw._type == "S":
            kw._value = _decode(record["valstr"])
        return kw


def _int_field(key):
    return property(lambda self: int(self._hdr[key][0]))


def _time_field(key):
    return property(lambda self: _datetime(self._hdr[key][0]))


class Image_md:
    """The image's metadata, read from the mapped memory on every access, as
    the binding's is, so a reference held across writes sees them."""
    def __init__(self, hdr):
        self._hdr = hdr

    version = property(lambda self: _decode(self._hdr["version"][0]))
    name = property(lambda self: _decode(self._hdr["name"][0]))
    naxis = _int_field("naxis")
    nelement = _int_field("nelement")
    shared = _int_field("shared")
    location = _int_field("location")
    status = _int_field("status")
    inode = _int_field("inode")
    logflag = _int_field("logflag")
    sem = _int_field("sem")
    cnt0 = _int_field("cnt0")
    cnt1 = _int_field("cnt1")
    cnt2 = _int_field("cnt2")
    write = _int_field("write")
    flag = _int_field("flag")
    NBkw = _int_field("NBkw")
    creationtime = _time_field("creationtime")
    lastaccesstime = _time_field("lastaccesstime")
    acqtime = _time_field("acqtime")
    writetime = _time_field("writetime")

    @property
    def size(self):
        return [int(s) for s in self._hdr["size"][0][:self.naxis]]

    @property
    def datatype(self):
        return ImageStreamIODataType(int(self._hdr["datatype"][0])).type

    @property
    def imagetype(self):
        return ImageStreamIOType(int(self._hdr["imagetype"][0])).type

    @property
    def location_str(self):
        return "CPU RAM" if self.location < 0 else f"GPU{self.location} RAM"

    def __repr__(self):
        fmt = "%a %b %d %H:%M:%S %Y"
        return "\n".join([
            f"Name: {self.name}",
            f"Version: {self.version}",
            f"Size: [{', '.join(str(s) for s in self.size)}]",
            f"nelement: {self.nelement}",
            f"creationtime: {self.creationtime.strftime(fmt)}",
            f"lastaccesstime: {self.lastaccesstime.strftime(fmt)}",
            f"acqtime: {self.acqtime.strftime(fmt)}",
            f"shared: {self.shared}",
            f"location: {self.location_str}",
            f"flag: {self.flag}",
            f"logflag: {self.logflag}",
            f"sem: {self.sem}",
            f"cnt0: {self.cnt0}",
            f"cnt1: {self.cnt1}",
            f"cnt2: {self.cnt2}",
        ])


class Image:
    def __init__(self):
        # Guards the semaphores between threads; flock only excludes other
        # open file descriptions, and threads here share one.
        self._lock = threading.RLock()
        self._reset()

    def _reset(self):
        self._backing = None  # an mmap for a shared image, a bytearray for a local one
        self._fd = None
        self._path = None
        self._memsize = 0
        self._hdr = None
        self._md = None
        self._semval = None
        self._sem_read_pid = None
        self._sem_write_pid = None
        self._kw = None
        self._data = None

    def _require(self):
        if self._data is None:
            raise RuntimeError("image not initialized")

    def _attach(self, backing, fd=None, path=None):
        if len(backing) <= _HEADER.itemsize:
            raise _BadFile("too small")
        hdr = np.frombuffer(backing, dtype=_HEADER, count=1)
        if hdr["magic"][0] != _MAGIC or hdr["layout"][0] != _LAYOUT_VERSION:
            raise _BadFile("not an isio_mock image")
        naxis = int(hdr["naxis"][0])
        shape = tuple(int(s) for s in hdr["size"][0][:naxis])
        dtype = _NUMPY_DTYPES[int(hdr["datatype"][0])]
        nsem = int(hdr["sem"][0])
        layout = _Layout(nsem, int(hdr["NBkw"][0]), int(np.prod(shape)) * dtype.itemsize)
        if len(backing) != layout.total:
            raise _BadFile("size does not match its header")
        self._semval = np.frombuffer(backing, "<i4", nsem, layout.semval)
        self._sem_read_pid = np.frombuffer(backing, "<i4", nsem, layout.sem_read_pid)
        self._sem_write_pid = np.frombuffer(backing, "<i4", nsem, layout.sem_write_pid)
        self._kw = np.frombuffer(backing, _KEYWORD, int(hdr["NBkw"][0]), layout.kw)
        self._data = np.ndarray(shape, dtype=dtype, buffer=backing,
                                offset=layout.data, order="F")
        self._hdr = hdr
        self._md = Image_md(hdr)
        self._backing, self._fd, self._path = backing, fd, path
        self._memsize = layout.total if fd is not None else 0

    def _release(self):
        backing, fd = self._backing, self._fd
        self._reset()
        if isinstance(backing, mmap.mmap):
            try:
                backing.close()
            except BufferError:
                # Something still views the memory (np.asarray(img), a held
                # md); the mapping goes when the last of those does.
                pass
        if fd is not None:
            os.close(fd)

    @contextlib.contextmanager
    def _sem_lock(self):
        with self._lock:
            if self._fd is None:
                yield
                return
            fcntl.flock(self._fd, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(self._fd, fcntl.LOCK_UN)

    @property
    def used(self):
        return 0 if self._data is None else 1

    @property
    def memsize(self):
        return self._memsize

    @property
    def md(self):
        return self._md

    @property
    def shape(self):
        self._require()
        return self._data.shape

    @property
    def semReadPID(self):
        self._require()
        return [int(pid) for pid in self._sem_read_pid]

    @property
    def semWritePID(self):
        self._require()
        return [int(pid) for pid in self._sem_write_pid]

    # Only circular buffers carry these, and the mock has none.
    @property
    def acqtimearray(self):
        self._require()
        raise RuntimeError("acqtimearray not initialized")

    @property
    def writetimearray(self):
        self._require()
        raise RuntimeError("writetimearray not initialized")

    @property
    def cntarray(self):
        self._require()
        raise RuntimeError("cntarray not initialized")

    def get_kws(self):
        return {kw.name: kw for kw in self.get_kws_list()}

    def get_kws_list(self):
        self._require()
        keywords = []
        for record in self._kw:
            if not record["name"]:
                break
            keywords.append(Image_kw._from_record(record))
        return keywords

    def set_kws(self, keywords):
        # The binding goes through a std::map, so keywords land sorted by name.
        self.set_kws_list([kw for _, kw in sorted(keywords.items())])

    def set_kws_list(self, keywords):
        self._require()
        count = 0
        for kw in keywords:
            if not isinstance(kw, Image_kw):
                raise TypeError("set_kws_list(): incompatible function arguments")
            if count >= len(self._kw):
                raise RuntimeError("Too many keywords provided")
            kw._to_record(self._kw[count])
            count += 1
        if count < len(self._kw):
            Image_kw()._to_record(self._kw[count])

    def __buffer__(self, flags):
        self._require()
        return memoryview(self._data)

    def copy(self):
        self._require()
        return self._data.copy(order="F")

    def _update(self, atime_ns):
        hdr = self._hdr
        if hdr["shared"][0] == 1:
            now = time.time_ns()
            hdr["writetime"] = now
            hdr["acqtime"] = now if atime_ns is None else atime_ns
            hdr["cnt0"] += 1
            hdr["write"] = 0
            self.sempost(-1)
        return IMAGESTREAMIO_SUCCESS

    def update(self):
        self._require()
        return self._update(None)

    def update_atime(self, tp):
        self._require()
        return self._update(int(tp.timestamp()) * 10**9 + tp.microsecond * 1000)

    def write(self, buffer):
        self._require()
        arr = np.asarray(buffer)
        if arr.dtype != self._data.dtype:
            raise ValueError("incompatible type")
        if arr.ndim != self._data.ndim:
            raise ValueError("incompatible number of axis")
        if arr.shape != self._data.shape:
            raise ValueError("incompatible shape")
        hdr = self._hdr
        hdr["write"] = 1
        self._data[...] = arr
        # Posting before the counters move is the binding's order too, so a
        # reader woken here can briefly still see the previous cnt0.
        self.sempost(-1)
        hdr["lastaccesstime"] = time.time_ns()
        hdr["write"] = 0
        hdr["cnt0"] += 1
        hdr["cnt1"] += 1

    def create(self, name, buffer, location=-1, shared=1,
               NBsem=IMAGE_NB_SEMAPHORE, NBkw=1, imagetype=_MATH_DATA, CBsize=0):
        try:
            memoryview(buffer)
        except TypeError:
            raise TypeError("create(): incompatible function arguments; "
                            "buffer must support the buffer protocol") from None
        arr = np.asarray(buffer)
        datatype = _datatype_of(arr.dtype)
        if datatype is None:
            raise RuntimeError("PyFormatToImageStreamIODataType -- Not implemented "
                               "datatype (possibly endianess issue.)")
        if location >= 0:
            raise NotImplementedError("isio_mock has no GPU images; location must be -1")
        if CBsize:
            raise NotImplementedError("isio_mock has no circular buffers; CBsize must be 0")
        if not name or not 1 <= arr.ndim <= 3:
            print(f"ERROR: cannot create image \"{name}\" with {arr.ndim} axes")
            return IMAGESTREAMIO_INVALIDARG
        if self._data is not None:
            self._release()

        layout = _Layout(NBsem, NBkw, arr.nbytes)
        if shared == 1:
            path = _filename(name)
            # Build the file aside and move it into place, so a process that
            # has the previous image of this name open keeps a whole one.
            fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path),
                                            prefix=f".{name}.", suffix=".tmp")
            os.ftruncate(fd, layout.total)
            backing = mmap.mmap(fd, layout.total)
        else:
            path = tmp_path = fd = None
            backing = bytearray(layout.total)

        hdr = np.frombuffer(backing, dtype=_HEADER, count=1)
        now = time.time_ns()
        hdr["magic"] = _MAGIC
        hdr["layout"] = _LAYOUT_VERSION
        hdr["version"] = IMAGESTRUCT_VERSION.encode()
        hdr["name"] = name.encode()
        hdr["naxis"] = arr.ndim
        hdr["size"][0][:arr.ndim] = arr.shape
        hdr["nelement"] = arr.size
        hdr["datatype"] = datatype
        hdr["imagetype"] = imagetype
        hdr["shared"] = 1 if shared == 1 else 0
        hdr["location"] = location
        hdr["sem"] = NBsem
        hdr["NBkw"] = NBkw
        hdr["creationtime"] = now
        hdr["lastaccesstime"] = now
        if fd is not None:
            hdr["inode"] = os.fstat(fd).st_ino
        del hdr  # _attach makes its own; this one would pin the mmap open
        self._attach(backing, fd, path)
        self.write(arr)
        if tmp_path is not None:
            os.replace(tmp_path, path)
        return IMAGESTREAMIO_SUCCESS

    def open(self, name):
        if self._data is not None:
            self._release()
        path = _filename(name)
        try:
            fd = os.open(path, os.O_RDWR)
        except OSError:
            print(f" [ WARNING ] Cannot open shm file \"{path}\"")
            return IMAGESTREAMIO_FILEOPEN
        backing = None
        try:
            size = os.fstat(fd).st_size
            if size <= _HEADER.itemsize:
                raise _BadFile("too small")
            backing = mmap.mmap(fd, size)
            self._attach(backing, fd, path)
        except _BadFile as err:
            print(f"ERROR: \"{path}\": {err}")
            self._reset()
            if backing is not None:
                with contextlib.suppress(BufferError):
                    backing.close()
            os.close(fd)
            return IMAGESTREAMIO_FILEOPEN
        return IMAGESTREAMIO_SUCCESS

    def close(self):
        self._require()
        self._release()
        return IMAGESTREAMIO_SUCCESS

    def destroy(self):
        self._require()
        path = self._path
        self._release()
        if path is not None:
            with contextlib.suppress(FileNotFoundError):
                os.remove(path)
        return IMAGESTREAMIO_SUCCESS

    def _sem_index_ok(self, index):
        if 0 <= index < len(self._semval):
            return True
        print(f"ERROR: image {self._md.name} semaphore # {index} does not exist")
        return False

    def _post(self, index):
        with self._sem_lock():
            if self._semval[index] < SEMAPHORE_MAXVAL:
                self._semval[index] += 1
                self._sem_write_pid[index] = os.getpid()

    def _trywait(self, index):
        with self._sem_lock():
            if self._semval[index] > 0:
                self._semval[index] -= 1
                return True
            return False

    def _wait(self, index, deadline):
        delay = _POLL_MIN_SEC
        while not self._trywait(index):
            if deadline is not None and time.monotonic() >= deadline:
                return -1
            time.sleep(delay)
            delay = min(delay * 2, _POLL_MAX_SEC)
        return 0

    def getsemwaitindex(self, index):
        self._require()
        pid = os.getpid()
        with self._sem_lock():
            readers = self._sem_read_pid
            for semindex, reader in enumerate(readers):
                if reader == pid:
                    return semindex
            candidates = range(len(readers))
            if 0 <= index < len(readers):
                candidates = [index, *candidates]
            for semindex in candidates:
                if readers[semindex] == 0 or not _pid_alive(int(readers[semindex])):
                    readers[semindex] = pid
                    return semindex
        return -1

    def semwait(self, index):
        self._require()
        if not self._sem_index_ok(index):
            return EXIT_FAILURE
        _warn_if_wait_blocks_others("semwait")
        return self._wait(index, None)

    def semtimedwait(self, index, timeoutsec):
        self._require()
        if not self._sem_index_ok(index):
            return EXIT_FAILURE
        if timeoutsec > 0:
            _warn_if_wait_blocks_others("semtimedwait")
        return self._wait(index, time.monotonic() + timeoutsec)

    def semtrywait(self, index):
        self._require()
        if not self._sem_index_ok(index):
            return EXIT_FAILURE
        return 0 if self._trywait(index) else -1

    def sempost(self, index=-1):
        self._require()
        if index < 0:
            for semindex in range(len(self._semval)):
                self._post(semindex)
        elif self._sem_index_ok(index):
            self._post(index)
        return IMAGESTREAMIO_SUCCESS

    def semflush(self, index):
        self._require()
        if index < 0:
            indices = range(len(self._semval))
        elif self._sem_index_ok(index):
            indices = [index]
        else:
            indices = []
        with self._sem_lock():
            for semindex in indices:
                self._semval[semindex] = 0
        return IMAGESTREAMIO_SUCCESS

    def semvalue(self, index):
        self._require()
        if not self._sem_index_ok(index):
            return -1
        return int(self._semval[index])
