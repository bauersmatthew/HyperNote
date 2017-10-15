"""Implement a representation for linked notes."""
from collections import namedtuple
import copy
import utils

Pos = namedtuple('Pos', ('start', 'end')) # start, end are ints
Link = namedtuple('Link', ('pos', 'dest')) # pos is Pos; dest is UID

class LinkedText:
    """Represents text with links in it."""
    def __init__(self):
        """Initialize an empty LinkedText."""
        self.text = ''
        self.links = []

    def __add__(self, other):
        """Add two LinkedText instances together."""
        off = len(self.text)
        c_text = self.text + other.text
        c_links = copy.copy(self.links)
        for link in other:
            c_links.append(Link(Pos(link.pos.start+off,
                                    link.pos.end+off),
                                link.dest))
        ret = LinkedText()
        ret.text = c_text
        ret.links = c_links
        return ret

    def __iter__(self):
        """Iterate over all our links."""
        yield from self.links

    def __getitem__(pos):
        """Get the string corresponding to the given link pos."""
        return self.text[pos.start:pos.end]

    def __getstate__(self):
        """Get the pickling state."""
        return dict(
            text=self.text,
            links=self.links)

    def __setstate__(self, state):
        """Set the state from pickled info."""
        self.text = state['text']
        self.links = state['links']

Part = namedtuple('Part', (
    'name', # str
    'display_name', # str or None
    'do_autolink', # 'str; 'unlinked' or 'autolinked'
))



AUTOFILL = ''
AUTOFILL_SAFETY = '@@'

SIG_OK = 0 # not an actual flag
FSF_INSUFFICIENT_INFO = (1 << 0)
FSF_AUTOFILL_UNSURE = (1 << 1)
FSF_AUTOFILL_FAILED = (1 << 2)
class Signal:
    """A signal raised by the __init__ method of Note classes."""
    def __init__(self, sig):
        self.sig = sig
    def __int__(self):
        return self.sig

class Note:
    """Represents a generalized pickleable note."""
    def __init__(self, uid, vals):
        """Initialize from plain text values."""
        self.uid = uid
        # check required attributes
        for attr in self.required:
            if attr not in vals:
                raise Signal(FSF_INSUFFICIENT_INFO)

        # try autofill
        sig = None
        try:
            self.autofill(vals)
        except Signal as s:
            sig = s

        self.fill(vals)
        raise sig

    def __getstate__(self):
        """Get the pickling state."""
        state = {}
        for name in self.parts:
            state[name] = getattr(self, name)
        state['uid'] = self.uid
        return state
    def __setstate__(self, state):
        """Set the state from pickled info."""
        for name in state:
            setattr(self, name, state[name])
        self.uid = state['uid']

    def fill(self, vals):
        """Fill self with values according to parts info."""
        for part in self.parts:
            val = vals[part.name]
            # IGNORE LINKING FOR NOW
            # TODO: AUTOMATIC LINKING
            lt = LinkedText()
            lt.text = val
            setattr(self, part.name, lt)

class ToolNote(Note):
    """Represents a note about a tool."""
    parts = (
        Part('name', 'Name', 'unlinked'),
        Part('cmd', 'Command', 'unlinked'),
        Part('ver', 'Version', 'unlinked'),
        Part('desc', 'Description', 'autolink'))

    searchable = ('name', 'cmd')
    required = ('cmd',)

    def autofill(self, vals):
        """Attempt to autofill empty values."""
        send = SIG_OK

        if vals['name'] == AUTOFILL:
            vals['name'] = vals.cmd

        if vals['ver'] == AUTOFILL_SAFETY:
            ver = utils.autodetect_version(vals['cmd'])
            if ver is None or ver == '':
                send |= FSF_AUTOFILL_FAILED
            else:
                vals['ver'] = ver
                send |= FSF_AUTOFILL_UNSURE

        raise Signal(send)

class ActionNote(Note):
    """Represents a note about a command run (action taken)."""
    parts = (
        Part('shellcmd', 'Shell command', 'linked'),
        Part('toolcmd', 'Tool', 'linked'),
        Part('time', 'Time', 'unlinked'),
        Part('desc', 'Description', 'linked'))

    required = ('shellcmd',)
    searchable = tuple()

    def autofill(self, vals):
        """Attempt to autofill empty values."""
        send = SIG_OK

        if vals['toolcmd'] == AUTOFILL:
            vals['toolcmd'] = vals['shellcmd'].split(' ')[0]
        if vals['time'] == AUTOFILL:
            vals['time'] = utils.get_timestamp()
            
        raise Signal(send)

class DataNote(Note):
    """Represents a note about a data file."""
    parts = (
        Part('name', 'Name', 'unlinked'),
        Part('path', 'Path', 'unlinked'),
        Part('src', 'Source', 'linked'), # kind of like a secondary description
        Part('desc', 'Description', 'linked'))

    searchable = ('name', 'path')
    required = ('path',)

    def autofill(self, vals):
        """Attempt to autofill empty values."""
        send = SIG_OK

        if vals['name'] == AUTOFILL:
            vals['name'] = vals['path'].split('/')[-1]

        self.fill(vals)

