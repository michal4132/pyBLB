import ctypes
import os
import sys
import platform

class TDataInfo(ctypes.Structure):
    _fields_ = [('pbInBuff', ctypes.POINTER(ctypes.c_ubyte)),
                ('pbInBuffEnd', ctypes.POINTER(ctypes.c_ubyte)),
                ('pbOutBuff', ctypes.POINTER(ctypes.c_ubyte)),
                ('pbOutBuffEnd', ctypes.POINTER(ctypes.c_ubyte))]

if(platform.system() == "Linux"):
    dll_name = "./pklib/pklib.so"
else:
    dll_name = "./pklib/pklib.32.dll"

dll = ctypes.CDLL(dll_name)

dll.implode.restype = ctypes.c_uint
dll.implode.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte),
                        ctypes.POINTER(TDataInfo),
                        ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]

dll.explode.restype = ctypes.c_int
dll.explode.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_ubyte),
                        ctypes.POINTER(TDataInfo)]

import struct

TESTSIZE = 1000 * 1000 * 32  # reserve 32mb

@ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(TDataInfo))
def write(buf, size, param):
    info = param.contents
    nMaxWrite = ctypes.cast(info.pbOutBuffEnd, ctypes.c_void_p).value - ctypes.cast(info.pbOutBuff,
                                                                                    ctypes.c_void_p).value
    nToWrite = size.contents.value

    if nToWrite > nMaxWrite:
        nToWrite = nMaxWrite

    for i in range(nToWrite):
        info.pbOutBuff[i] = buf[i]

    ctypes.cast(ctypes.pointer(info.pbOutBuff), ctypes.POINTER(ctypes.c_void_p)).contents.value += nToWrite

    return None


@ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_ubyte), ctypes.POINTER(ctypes.c_uint),
                  ctypes.POINTER(TDataInfo))
def read(buf, size, param):
    info = param.contents
    nMaxAvail = ctypes.cast(info.pbInBuffEnd, ctypes.c_void_p).value - ctypes.cast(info.pbInBuff,
                                                                                   ctypes.c_void_p).value
    nToRead = size.contents.value

    if nToRead > nMaxAvail:
        nToRead = nMaxAvail

    for i in range(nToRead):
        buf[i] = info.pbInBuff[i]

    ctypes.cast(ctypes.pointer(info.pbInBuff), ctypes.POINTER(ctypes.c_void_p)).contents.value += nToRead

    return nToRead


def decompress(data):
    indata = data

    work_buf = (ctypes.c_ubyte * (12596 + 100))()
    work_buf = ctypes.cast(work_buf, ctypes.POINTER(ctypes.c_ubyte))

    info = TDataInfo()

    info.pbInBuff = ctypes.cast(indata, ctypes.POINTER(ctypes.c_ubyte))
    info.pbInBuffEnd = ctypes.cast(
        ctypes.cast(ctypes.cast(info.pbInBuff, ctypes.c_void_p).value + len(indata), ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_ubyte))

    outdata = b'\x00' * TESTSIZE

    info.pbOutBuff = ctypes.cast(outdata, ctypes.POINTER(ctypes.c_ubyte))
    info.pbOutBuffEnd = ctypes.cast(
        ctypes.cast(ctypes.cast(info.pbOutBuff, ctypes.c_void_p).value + TESTSIZE, ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_ubyte))

    ob = ctypes.cast(info.pbOutBuff, ctypes.c_void_p).value

    result = dll.explode(read, write, work_buf, info)

    if result != 0:
        raise Exception("conversion returned {}".format(result))

    decompressed_size = ctypes.cast(info.pbOutBuff, ctypes.c_void_p).value - ob

    r = outdata[0:decompressed_size]
    return b''.join(struct.pack("B", v) for v in r)

def compress(data):
    indata = data

    work_buf = (ctypes.c_ubyte * (36312 + 100))()
    work_buf = ctypes.cast(work_buf, ctypes.POINTER(ctypes.c_ubyte))

    info = TDataInfo()

    info.pbInBuff = ctypes.cast(indata, ctypes.POINTER(ctypes.c_ubyte))
    addr = ctypes.cast(info.pbInBuff, ctypes.c_void_p).value
    newaddr = ctypes.cast(info.pbInBuff, ctypes.c_void_p).value + len(indata)
    pvoid = ctypes.cast(newaddr, ctypes.c_void_p)
    info.pbInBuffEnd = ctypes.cast(pvoid, ctypes.POINTER(ctypes.c_ubyte))

    outdata = b'\x00' * TESTSIZE

    info.pbOutBuff = ctypes.cast(outdata, ctypes.POINTER(ctypes.c_ubyte))
    addr = ctypes.cast(info.pbOutBuff, ctypes.c_void_p).value
    newaddr = ctypes.cast(info.pbOutBuff, ctypes.c_void_p).value + TESTSIZE
    pvoid = ctypes.cast(newaddr, ctypes.c_void_p)
    info.pbOutBuffEnd = ctypes.cast(pvoid, ctypes.POINTER(ctypes.c_ubyte))

    ob = ctypes.cast(info.pbOutBuff, ctypes.c_void_p).value
    oa = ctypes.addressof(info.pbOutBuff)

    dsize = ctypes.c_uint(4096)
    type = ctypes.c_uint(1)

    result = dll.implode(read, write, work_buf, info, type, dsize)

    compressed_size = ctypes.cast(info.pbOutBuff, ctypes.c_void_p).value - ob

    if result != 0:
        raise Exception("conversion returned {}".format(result))

    od = (ctypes.c_ubyte * compressed_size).from_address(ob)
    r = od[0:compressed_size]

    return b''.join(struct.pack("B", v) for v in r)
