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

class CreationStatus:
    """Extra info associated with the de novo creation of a Note."""
    def __init__(self,
                 insufficient_info=False, autofill_failed=False,
                 autofill_unsure=False, unsure_fields=[]):
        self.insufficient_info = insufficient_info
        self.autofill_failed = autofill_failed
        self.autofill_unsure = autofill_unsure
        self.unsure_fields = copy.copy(unsure_fields)

    def __bool__(self):
        """Return true if good; false if failed."""
        return (not self.insufficient_info) and (not self.autofill_failed)

    def __str__(self):
        """Return an empty string if no FATAL error were encountered."""
        if self:
            return ''
        msg = 'Note creation error:\n'
        num = 1
        if self.insufficient_info:
            msg += str(num) + \
                   '. Insufficient info given (required fields omitted).\n'
            num += 1
        if self.autofill_failed:
            msg += str(num) + \
                   '. Autofill failed.\n'
        return msg

class CreationFailure(Exception):
    """Exception associated with failing to create a Note de novo.

    Essentially just wraps a CreationStatus. The intent is to not allow
    anyone from keeping around references to invalid notes."""
    def __init__(self, cstatus):
        self.status = cstatus

class Note:
    """Represents a generalized pickleable note."""
    def __init__(self, uid, vals):
        """Initialize from plain text values."""
        self.uid = uid
        self.cstatus = CreationStatus()

        # check required attributes
        for attr in self.required:
            if attr not in vals:
                self.signal = Signal(FSF_INSUFFICIENT_INFO)
                return

        # try autofill
        self.autofill(vals) # edits cstatus

        # fill into object attributes
        self.fill(vals)

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
    unsafe = ('ver',)

    def autofill(self, vals):
        """Attempt to autofill empty values."""
        if vals['name'] == AUTOFILL:
            vals['name'] = vals['cmd']

        if vals['ver'] == AUTOFILL_SAFETY:
            ver = utils.autodetect_version(vals['cmd'])
            if ver is None or ver == '':
                self.cstatus.autofill_failed = True
            else:
                vals['ver'] = ver
                self.cstatus.autofill_unsure = True
                self.cstatus.unsure_fields.append('ver')

class ActionNote(Note):
    """Represents a note about a command run (action taken)."""
    parts = (
        Part('shellcmd', 'Shell command', 'linked'),
        Part('toolcmd', 'Tool', 'linked'),
        Part('time', 'Time', 'unlinked'),
        Part('desc', 'Description', 'linked'))

    required = ('shellcmd',)
    searchable = tuple()
    unsafe = tuple()

    def autofill(self, vals):
        """Attempt to autofill empty values."""
        if vals['toolcmd'] == AUTOFILL:
            vals['toolcmd'] = vals['shellcmd'].split(' ')[0]
        if vals['time'] == AUTOFILL:
            vals['time'] = utils.get_timestamp()

class DataNote(Note):
    """Represents a note about a data file."""
    parts = (
        Part('name', 'Name', 'unlinked'),
        Part('path', 'Path', 'unlinked'),
        Part('src', 'Source', 'linked'), # kind of like a secondary description
        Part('desc', 'Description', 'linked'))

    searchable = ('name', 'path')
    required = ('path',)
    unsafe = tuple()

    def autofill(self, vals):
        """Attempt to autofill empty values."""
        if vals['name'] == AUTOFILL:
            vals['name'] = vals['path'].split('/')[-1]
