"""Handle registry input/output, including multiversion compatibility."""
from hypernote import note
from collections import OrderedDict
import struct
import string
from functools import wraps
from datetime import datetime

# dictionary (type -> function) of all encoders
encoders = {}

def encoder(dtype):
    """Wrapper for encoder functions."""
    def encoder_wrapper(inner):
        name = inner.__name__
        parts = name.split('_')
        typecode = parts[1]
        version = parts[2]

        @wraps(inner)
        def fun(v):
            data = inner(v)
            typecode_b = bytes(typecode, 'utf8')
            version_b = struct.pack('<i', int(version)) # store version as int
            return typecode_b + version_b + data
        fun.__name__ = inner.__name__
        fun.__doc__ = inner.__doc__

        global encoders
        encoders[dtype] = fun
        return fun
    return encoder_wrapper

def get_encoder(dtype):
    """Get the encoder corresponding to the given datatype."""
    return encoders[dtype]

# dictionary (typecode -> function) of all decoders
decoders  = {}

def decoder(inner):
    """Wrapper for decoder functions."""
    name = inner.__name__
    parts = name.split('_')
    typecode = parts[1]
    version = int(parts[2])

    global decoders
    decoders[typecode, version] = inner
    return inner

def get_decoder(typecode, version):
    """Get the decoder corresponding to the given typecode and version."""
    return decoders[typecode, version]

def load_object(b):
    """Load the next object present in the given bytearray."""
    tc = extract_typecode(b)
    ver = extract_version(b)
    dec = get_decoder(tc, ver)
    obj = dec(b)
    return obj

# ----------------------
# ------ ENCODERS ------
# ----------------------
def encode_from_datascheme(n, scheme):
    """Encode a note from a datascheme."""
    data = bytes()
    for attr in scheme:
        val = getattr(n, attr)
        data += get_encoder(type(val))(val)
    return data

@encoder(str)
def e_s_1(s):
    """Encode a string."""
    b = get_encoder(int)(len(s))
    b += bytes(s, 'utf8')
    return b

@encoder(int)
def e_i_1(i):
    """Encode an int."""
    return struct.pack('<i', i)

@encoder(float)
def e_f_1(f):
    """Encode a float."""
    return struct.pack('<f', f)

@encoder(datetime)
def e_t_1(ts):
    """Encode a timestamp."""
    return get_encoder(float)(ts.timestamp())

@encoder(note.LinkedText)
def e_L_1(lt):
    """Encode LinkedText."""
    # first put text
    data = get_encoder(str)(lt.text)
    # then put links
    data += get_encoder(int)(len(lt.links))
    for link in lt.links:
        data += get_encoder(int)(link.pos.start)
        data += get_encoder(int)(link.pos.end)
        data += get_encoder(type(link.dest))(link.dest)
    return data

@encoder(note.ToolNote)
def e_T_1(n):
    """Encode a ToolNote."""
    return encode_from_datascheme(n, ('uid', 'name', 'cmd', 'ver', 'desc'))

@encoder(note.ActionNote)
def e_A_1(n):
    """Encode an ActionNote."""
    return encode_from_datascheme(
        n, ('uid', 'shellcmd', 'toolcmd', 'time', 'desc'))

@encoder(note.DataNote)
def e_D_1(n):
    """Encode a DataNote."""
    return encode_from_datascheme(n, ('uid', 'name', 'path', 'src', 'desc'))

# ----------------------
# ------ DECODERS ------
# ----------------------
def extract_typecode(data):
    """Extract a typecode from the beginning of the data."""
    tc = chr(data[0])
    del data[0]
    return tc
def extract_version(data):
    """Extract an encoding version from the beginning of the data."""
    ver = struct.unpack('<i', data[:4])[0]
    del data[:4]
    return ver

def decode_from_datascheme(data, dtype, scheme):
    """Encode a note from a datascheme."""
    # bypass calling the Note() constructor
    class EmptyClass:
        pass
    obj = EmptyClass()
    obj.__class__ = dtype
    for attr in scheme:
        try:
            setattr(obj, attr,
                    load_object(data))
        except:
            raise
    return obj

@decoder
def d_s_1(b):
    """Decode a string."""
    length = load_object(b) # int
    ret = b[:length].decode('utf8')
    del b[:length]
    return ret

@decoder
def d_i_1(b):
    """Decode an int."""
    ret = struct.unpack('<i', b[:4])[0]
    del b[:4]
    return ret

@decoder
def d_f_1(b):
    """Decode a float."""
    ret = struct.unpack('<f', b[:4])[0]
    del b[:4]
    return ret

@decoder
def e_t_1(b):
    """Decode a timestamp."""
    ts = load_object(b) # float
    return datetime.fromtimestamp(ts)

@decoder
def d_L_1(b):
    """Decode LinkedText."""
    text = load_object(b)
    lt = note.LinkedText(text)
    links_len = load_object(b)
    from hypernote.note import Pos
    for x in range(links_len):
        start = load_object(b)
        end = load_object(b)
        uid = load_object(b)
        lt.link(Pos(start, end), uid)
    return lt
    
@decoder
def d_T_1(d):
    """Decode a ToolNote."""
    return decode_from_datascheme(
        d, note.ToolNote,
        ('uid', 'name', 'cmd', 'ver', 'desc'))

@decoder
def d_A_1(d):
    """Decode an ActionNote."""
    return decode_from_datascheme(
        d, note.ActionNote,
        ('uid', 'shellcmd', 'toolcmd', 'time', 'desc'))

@decoder
def d_D_1(d):
    """Decode a DataNote."""
    return decode_from_datascheme(
        d, note.DataNote,
        ('uid', 'name', 'path', 'src', 'desc'))
