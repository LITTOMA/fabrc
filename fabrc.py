import struct
from io import BytesIO

from utils import align

class FabResourceBase(object):
    def __init__(self, fs):
        self.Magic, self.Size = struct.unpack('>4si', fs.read(8))
        self.Stream = fs
        # print 'Read', self.Magic, 'at', hex(fs.tell()-8)
        exec "self.__class__ = %s"%self.Magic
        if self.Size:
            self.__parse__()
    
    def __parse__(self):
        pass
    
    def tobin(self):
        pass

    def save(self, fs):
        data = self.tobin()
        fs.write(struct.pack('>4si', self.Magic, self.Size))
        fs.write(data)

class FBRC(FabResourceBase):
    def __parse__(self):
        base = self.Stream.tell()
        self.Desc = self.Stream.read(4)
        read_size = 4
        self.Members = []
        while read_size < self.Size:
            member = FabResourceBase(self.Stream)
            self.Members.append(member)
            read_size = self.Stream.tell() - base
            if not isinstance(member, LIST):
                exec 'self.%s = member'%(member.Magic.lower())
            else:
                exec 'self.%s = member'%(member.Desc.lower())

    def tobin(self):
        ms = BytesIO()
        ms.write(self.Desc)
        for member in self.Members:
            member.save(ms)
        self.Size = ms.tell()
        return ms.getvalue()

class LIST(FabResourceBase):
    def __parse__(self):
        base = self.Stream.tell()
        self.Desc = self.Stream.read(4)
        read_size = 4

        self.Items = []
        while read_size < self.Size:
            item = FabResourceBase(self.Stream)
            self.Items.append(item)
            al = align(self.Stream.tell(), 2)
            self.Stream.seek(al, 1)
            read_size = self.Stream.tell() - base

            code = '''if hasattr(self, "{name}"):
    if not isinstance(self.{name}, list):
        self.{name} = [self.{name}]
    self.{name}.append(item)
else:
    self.{name} = item'''.format(name=str(item.Magic).lower())
            exec code
    
    def tobin(self):
        ms = BytesIO()
        ms.write(self.Desc)
        for item in self.Items:
            item.save(ms)
        self.Size = ms.tell()
        return ms.getvalue()

class FabBoolBase(FabResourceBase):
    def __parse__(self):
        self.Value = bool(struct.unpack('<i', self.Stream.read(4))[0])
    
    def tobin(self):
        ms = BytesIO()
        ms.write(struct.pack('<i', int(self.Value)))
        self.Size = ms.tell()
        return ms.getvalue()

class FabIntBase(FabResourceBase):
    def __parse__(self):
        self.Value ,= struct.unpack('<i', self.Stream.read(4))
    
    def tobin(self):
        ms = BytesIO()
        ms.write(struct.pack('<i', int(self.Value)))
        self.Size = ms.tell()
        return ms.getvalue()

class FabStrBase(FabResourceBase):
    def __parse__(self):
        self.Value = self.Stream.read(self.Size)
        al = align(self.Stream.tell(), 2)
        self.Stream.seek(al, 1)

    def tobin(self):
        ms = BytesIO()
        ms.write(self.Value)
        self.Size = ms.tell()
        al = align(ms.tell(), 2)
        ms.write('\x00'*al)
        return ms.getvalue()

class BOLD(FabBoolBase):
    pass

class ITAL(FabBoolBase):
    pass

class PACK(FabBoolBase):
    pass

class CNT(FabIntBase):
    pass

class ENDI(FabIntBase):
    pass

class SIZE(FabIntBase):
    pass

class LINH(FabIntBase):
    pass

class PAGS(FabIntBase):
    pass

class KCNT(FabIntBase):
    pass

class VERS(FabResourceBase):
    def __parse__(self):
        self.Value = struct.unpack('BBBB', self.Stream.read(4))
    
    def tobin(self):
        ms = BytesIO()
        ms.write(struct.pack('BBBB', *self.Value))
        self.Size = ms.tell()
        return ms.getvalue()

class PLAT(FabStrBase):
    pass

class CPLT(FabStrBase):
    pass

class GPLT(FabStrBase):
    pass

class FACE(FabStrBase):
    pass

class TXTN(FabStrBase):
    def __parse__(self):
        super(TXTN, self).__parse__()
        self.page = FabResourceBase(self.Stream)
    
    def tobin(self):
        ms = BytesIO()
        ms.write(super(TXTN, self).tobin())
        self.page.save(ms)
        return ms.getvalue()

class GLYP(FabResourceBase):
    def __parse__(self):
        self.CharCode, _ = struct.unpack('HH', self.Stream.read(4))
        self.Attrs = struct.unpack('fffffffiiffffff', self.Stream.read(60))
        self.KerningCount = FabResourceBase(self.Stream)
        self.KerningData = FabResourceBase(self.Stream)
    
    def tobin(self):
        ms = BytesIO()
        
        ms.write(struct.pack('HH', self.CharCode, 0))
        ms.write(struct.pack('fffffffiiffffff', *self.Attrs))
        self.Size = ms.tell()

        self.KerningCount.save(ms)
        self.KerningData.save(ms)

        return ms.getvalue()

class KERN(FabResourceBase):
    def __parse__(self):
        self.Data = self.Stream.read(self.Size)

    def tobin(self):
        ms = BytesIO()
        if hasattr(self, 'Data'):
            ms.write(self.Data)
        self.Size = ms.tell()
        return ms.getvalue()

class TXMD(FabResourceBase):
    def __parse__(self):
        self.Attr = struct.unpack('i'*(self.Size/4), self.Stream.read(self.Size))

class PDAT(FabResourceBase):
    def __parse__(self):
        self.TexData = self.Stream.read(self.Size)

if __name__ == "__main__":
    fs = open('fabfonts/nintendo.fabfnt', 'rb')
    fbrc = FabResourceBase(fs)
    print fbrc.Desc
    
    fs2 = open('test.fbrc', 'wb')
    fbrc.save(fs2)
    fs2.close()
