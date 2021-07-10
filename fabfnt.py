from ctypes import resize
import os
import struct
from io import BytesIO

import freetype
import greedypacker
from freetype import (FT_LOAD_DEFAULT, FT_LOAD_NO_BITMAP, FT_LOAD_NO_HINTING,
                      FT_LOAD_RENDER, FT_RENDER_MODE_NORMAL, Face, Vector)
from PIL import Image

from fabrc import makeEntry, makeList, makeFbrc


def f26d6_to_int(val):
    ret = (abs(val) & 0x7FFFFFC0) >> 6
    if val < 0:
        return -ret
    else:
        return ret


def f16d16_to_int(val):
    ret = (abs(val) & 0x3FFFC0) >> 16
    if val < 0:
        return -ret
    else:
        return ret


class FabGlyph(object):
    def __init__(self) -> None:
        super().__init__()
        self.char = ''
        self.image = None
        self.width = 0
        self.height = 0
        self.xadv = 0
        self.xoffset = 0
        self.yoffset = 0
        self.packerItem = None
        self.page = -1
        self.containerWidth = 0
        self.containerHeight = 0

    def pack(self):
        return struct.pack('<ifffffffiiffffii', self.charcode, self.x, self.y,
                           self.width, self.height, self.xoffset, self.yoffset,
                           self.xadv, self.page, 0xF,
                           self.left, self.right, self.top, self.bottom,
                           0, 0)

    @property
    def charcode(self):
        return ord(self.char)

    @charcode.setter
    def charcode(self, value):
        self.char = chr(value)

    @property
    def x(self):
        return self.packerItem.x

    @property
    def y(self):
        return self.packerItem.y

    @property
    def left(self):
        return self.x / self.containerWidth

    @property
    def right(self):
        return (self.x+self.width)/self.containerWidth

    @property
    def top(self):
        return self.y/self.containerHeight

    @property
    def bottom(self):
        return (self.y+self.height)/self.containerHeight

    @staticmethod
    def new(char, font, baseline=0):
        result = FabGlyph()
        result.charcode = ord(char)

        char_index = font.get_char_index(char)
        if not char_index:
            # print(
            #     'WARNING: Cannot find glyph for char "\\u%04x" from any of given fonts.' % ord(char))
            char = '?'
        flags = FT_LOAD_RENDER
        font.load_char(char, flags)

        glyphslot = font.glyph
        bitmap = glyphslot.bitmap

        ascender = f26d6_to_int(font.size.ascender)
        fontHeight = f26d6_to_int(font.size.height)
        adv = f26d6_to_int(glyphslot.metrics.horiAdvance)
        horiBearingX = f26d6_to_int(glyphslot.metrics.horiBearingX)
        horiBearingY = f26d6_to_int(glyphslot.metrics.horiBearingY)

        image = Image.new('RGBA', (bitmap.width, bitmap.rows))
        for y in range(bitmap.rows):
            for x in range(bitmap.width):
                pos = y * bitmap.width + x
                a = ((bitmap.buffer[pos]) & 0xFF)
                image.putpixel((x, y), (a, a, a, a))

        result.width = image.width
        result.height = image.height
        result.xadv = adv
        result.xoffset = horiBearingX
        result.yoffset = fontHeight - horiBearingY - baseline
        result.image = image
        result.packerItem = greedypacker.Item(result.width, result.height)

        return result

    @staticmethod
    def fromimage(path):
        result = FabGlyph()
        result.image = Image.open(path)
        result.charcode = int(os.path.split(os.path.splitext(path)[0])[1])
        result.width = result.image.width
        result.height = result.image.height
        result.xadv = result.width
        result.xoffset = 0
        result.yoffset = 0
        result.packerItem = greedypacker.Item(result.width, result.height)
        return result


class FabFont(object):
    def __init__(self, name, width, height) -> None:
        super().__init__()
        self.ttf = None
        self.glyphs = {}
        self.name = name
        self.faceName = 'nintendo'
        self.imageWidth = width
        self.imageHeight = height
        self.imageCount = 0
        self.size = 0
        self.bold = 0
        self.italic = 0
        self.lineHight = 0
        self.pack = 0

    def addChar(self, char, font, baseline):
        if ord(char) in self.glyphs.keys():
            return

        g = FabGlyph.new(char, font, baseline)
        g.containerWidth = self.imageWidth
        g.containerHeight = self.imageHeight
        self.glyphs[g.charcode] = g

    def addGlyph(self, glyph):
        if glyph.charcode in self.glyphs:
            print('WARNING: Glyph <%x> already in font, overwritten.' %
                  glyph.charcode)
        glyph.containerWidth = self.imageWidth
        glyph.containerHeight = self.imageHeight
        self.glyphs[glyph.charcode] = glyph

    def save(self, dirname):
        names = []
        for i in range(self.imageCount):
            img = Image.new('RGBA', (self.imageWidth, self.imageHeight))
            for g in self.glyphs.values():
                if g.page != i:
                    continue
                img.paste(g.image, (g.x, g.y))
            name = '%s_%d' % (self.name, i)
            names.append(name)
            p = os.path.join(dirname, name+'.png')
            print('Save:', p)
            img.save(p)

        path = os.path.join(dirname, self.name+'.fabfnt')
        print('Save:', path)
        fntbin = open(path, 'wb')

        head = makeList('HEAD',
                        makeEntry('FACE', self.faceName.encode(
                            'ascii')+b'\x00'),
                        makeEntry('SIZE', struct.pack('<i', self.size)),
                        makeEntry('BOLD', struct.pack('<i', self.bold)),
                        makeEntry('ITAL', struct.pack('<i', self.italic)),
                        makeEntry('LINH', struct.pack('<i', self.lineHight)),
                        makeEntry('PAGS', struct.pack(
                            '<i', self.imageCount)),
                        makeEntry('PACK', struct.pack('<i', self.pack)))

        pageList = makeList('PAGL',
                            makeEntry('CNT ', struct.pack('<i', len(names))),
                            *(
                                (e for g in (
                                    (
                                        makeEntry('TXTN', name.encode(
                                            'ascii')+b'\x00'),
                                        makeList('PAGE', b'')
                                    )
                                    for name in names)
                                 for e in g)
                            ))

        glyphList = makeList('GLYL',
                             makeEntry('CNT ', struct.pack(
                                 '<i', len(self.glyphs))),
                             *(
                                 (e for g in (
                                     (
                                         makeEntry('GLYP', glyph.pack()),
                                         makeEntry(
                                             'KCNT', struct.pack('<i', 0)),
                                         makeEntry('KERN', b'')
                                     )
                                     for glyph in (self.glyphs[charcode] for charcode in sorted(self.glyphs.keys())))
                                  for e in g)
                             )
                             )

        fntbin.write(makeFbrc('FTYP',
                              makeList('META',
                                       makeEntry('ENDI', struct.pack('<i', 1)),
                                       makeEntry(
                                           'VERS', struct.pack('<i', 0x3e8)),
                                       makeEntry('PLAT', b'3DS '),
                                       makeEntry('CPLT', b'ARM '),
                                       makeEntry('GPLT', b'3DS ')
                                       ),
                              head,
                              pageList,
                              glyphList
                              ))

    @staticmethod
    def new(fontname, ttfPath, size, charset, imageGlyphs, baseline):
        charset = sorted(charset)

        fabfnt = FabFont(fontname, 512, 512)
        fabfnt.faceName = os.path.splitext(os.path.split(ttfPath)[1])[0]
        ttf = freetype.Face(ttfPath)
        ttf.set_pixel_sizes(size, size)

        for char in charset:
            fabfnt.addChar(char, ttf, baseline)
        for path in imageGlyphs:
            g = FabGlyph.fromimage(path)
            fabfnt.addGlyph(g)

        binMan = greedypacker.BinManager(
            fabfnt.imageWidth, fabfnt.imageHeight, pack_algo='skyline', heuristic='best_fit', rotation=False)
        binMan.add_items(*(g.packerItem for g in fabfnt.glyphs.values()))
        binMan.execute()

        fabfnt.imageCount = len(binMan.bins)

        for i in range(len(binMan.bins)):
            b = binMan.bins[i]
            for item in b.items:
                for g in fabfnt.glyphs.values():
                    if item is g.packerItem:
                        g.page = i
                        break

        fabfnt.size = size
        fabfnt.lineHight = size
        return fabfnt


def make_font(fontname, charset_path, charset_encoding, facepath, size, savedir, baseline, *imageGlyphs):
    s = open(charset_path, 'r', encoding=charset_encoding).read()
    fnt = FabFont.new(fontname, facepath, size, s, list(imageGlyphs), baseline)
    fnt.save(savedir)


if __name__ == '__main__':
    import fire
    fire.Fire(make_font)
