import lz4.block
import struct
from io import BytesIO

from msbt.utils import align


def makeEntry(name, *data):
    ms = BytesIO()
    ms.write(struct.pack('>4si', name.encode('ascii'), 0))
    for d in data:
        ms.write(d)
    size = ms.tell() - 8
    ms.seek(4, 0)
    ms.write(struct.pack('>i', size))
    return ms.getvalue()


def makeList(name, *entries):
    ms = BytesIO()
    ms.write(struct.pack('>4si4s', b'LIST', 0, name.encode('ascii')))
    for e in entries:
        ms.write(e)
        ms.write(b'\x00'*(align(ms.tell(), 2)-ms.tell()))
    size = ms.tell() - 8
    ms.seek(4, 0)
    ms.write(struct.pack('>i', size))
    return ms.getvalue()


def makeFbrc(name, *entries):
    ms = BytesIO()
    ms.write(struct.pack('>4si4s', b'FBRC', 0, name.encode('ascii')))
    for e in entries:
        ms.write(e)
        ms.write(b'\x00'*(align(ms.tell(), 2)-ms.tell()))
    size = ms.tell() - 8
    ms.seek(4, 0)
    ms.write(struct.pack('>i', size))
    return ms.getvalue()


def readEntry(stream):
    name = stream.read(4).decode('ascii')
    size, = struct.unpack('>i', stream.read(4))
    data = stream.read(size)
    stream.seek(align(stream.tell(), 2), 0)
    return name, BytesIO(data)


def readList(stream):
    sig = stream.read(4).decode('ascii')
    if sig != 'LIST':
        raise ValueError("invalid signature: "+sig)
    size, = struct.unpack('>i', stream.read(4))
    name = stream.read(4).decode('ascii')
    data = stream.read(size-4)
    stream.seek(align(stream.tell(), 2), 0)
    return name, BytesIO(data)


def readFbrc(stream):
    sig = stream.read(4).decode('ascii')
    if sig != 'FBRC':
        raise ValueError("invalid signature: "+sig)
    size, = struct.unpack('>i', stream.read(4))
    name = stream.read(4).decode('ascii')
    data = stream.read(size-4)
    stream.seek(align(stream.tell(), 2), 0)
    return name, BytesIO(data)


def readUser(stream):
    sig = stream.read(4).decode('ascii')
    if sig != 'USER':
        raise ValueError("invalid signature: "+sig)
    size, = struct.unpack('>i', stream.read(4))
    name = stream.read(4).decode('ascii')
    data = stream.read(size-4)
    stream.seek(align(stream.tell(), 2), 0)
    if name == 'LZ4C':
        uncomp_size, comp_size = struct.unpack('<ii', data[:8])
        if uncomp_size < 0:
            uncomp_size = ~uncomp_size + 1
        data = lz4.block.decompress(data[8:8+comp_size], uncompressed_size=uncomp_size)
    return name, BytesIO(data)


def readInt(stream):
    name, dataStream = readEntry(stream)
    value, = struct.unpack('<i', dataStream.read(4))
    return name, value
