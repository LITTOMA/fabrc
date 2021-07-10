from fabrc import *
import struct


def ctpk2fabtex(ctpk, fabtex):
    FMT = {0xA: 0x401042, 0xB: 0x401042, 0xD: 0x801030}

    ctpk = open(ctpk, 'rb').read()
    fmt, w, h = struct.unpack('<ihh', ctpk[0x2C:0x34])
    if fmt not in FMT:
        raise ValueError('Unsupported format: '+str(fmt))

    fbrc = makeFbrc('TXTR',
                    makeList('META',
                             makeEntry('ENDI', struct.pack('<i', 1)),
                             makeEntry(
                                 'VERS', struct.pack('<i', 0)),
                             makeEntry('PLAT', b'3DS '),
                             makeEntry('CPLT', b'ARM '),
                             makeEntry('GPLT', b'3DS ')
                             ),
                    makeEntry('TXMD', struct.pack('<iiiiiiiiii',
                              1, w, h, 1, 1, 1, 1, 0, FMT[fmt], 0)),
                    makeEntry('PDAT', ctpk)
                    )
    open(fabtex, 'wb').write(fbrc)


if __name__ == '__main__':
    import fire
    fire.Fire(ctpk2fabtex)
