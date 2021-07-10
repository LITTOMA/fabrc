from io import BytesIO
import struct
from fabrc import *
import os
import sys


def readBundle(path):
    fs = open(path, 'rb')
    name, dataStream = readFbrc(fs)
    if name != 'BNDL':
        raise 'invalid resource: '+name
    _, fileCount = readEntry(dataStream)
    fileCount, = struct.unpack('>i', fileCount.getvalue())

    entries = []
    for i in range(fileCount):
        _, entryData = readList(dataStream)
        _, fileName = readEntry(entryData)
        fileName = fileName.getvalue().decode('ascii').replace('\0', '')
        _, fileData = readList(entryData)
        entries.append([fileName, fileData.getvalue()])
    return entries


class actions(object):
    @staticmethod
    def unpack(path, path_out, decompress=False):
        entries = readBundle(path)
        for e in entries:
            data = e[1]
            unpack_path = os.path.join(path_out, e[0])
            sys.stdout.write('Extract: '+unpack_path)
            if not os.path.exists(path_out):
                os.makedirs(path_out)
            if decompress:
                if data[:4].decode('ascii') == 'USER':
                    _, data = readUser(BytesIO(data))
                    data = data.getvalue()
                    sys.stdout.write(' [decompressed]')
            open(unpack_path, 'wb').write(data)
            print('')

    @staticmethod
    def pack(path, path_out):
        files = os.listdir(path)

        entries = {}
        for fp in files:
            rp = os.path.join(path, fp)
            print('Load:', rp)
            data = open(rp, 'rb').read()
            entries[fp] = data

        bundle = makeFbrc('BNDL',
                          makeEntry('NUM ', struct.pack('>i', len(files))),
                          *(
                              makeList('FILE',
                                       makeEntry('NAME', fileName.encode(
                                           'ascii')),
                                       makeList('DATA', entries[fileName])
                                       )

                              for fileName in entries.keys()
                          )
                          )
        open(path_out, 'wb').write(bundle)

    @staticmethod
    def repack(path, load_dir, path_out):
        entries = readBundle(path)
        for e in entries:
            loadPath = os.path.join(load_dir, e[0])
            if os.path.isfile(loadPath):
                print('Load:', loadPath)
                e[1] = open(loadPath, 'rb').read()

        bundle = makeFbrc('BNDL',
                          makeEntry('NUM ', struct.pack('>i', len(entries))),
                          *(
                              makeList('FILE',
                                       makeEntry('NAME', e[0].encode(
                                           'ascii')),
                                       makeList('DATA', e[1])
                                       )

                              for e in entries
                          )
                          )
        open(path_out, 'wb').write(bundle)


if __name__ == '__main__':
    import fire
    fire.Fire(actions)
