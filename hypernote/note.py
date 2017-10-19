"""Implement a representation for linked notes."""
from collections import namedtuple
import copy
from hypernote import utils
from hypernote import registry

Pos = namedtuple('Pos', ('start', 'end')) # start, end are ints
Link = namedtuple('Link', ('pos', 'dest')) # pos is Pos; dest is UID

class LinkedText:
    """Represents text with links in it."""
    def __init__(self, text=''):
        """Initialize an empty LinkedText."""
        self.text = text
        self.links = []

    def link(self, pos, uid):
        """Add a link at the given position."""
        self.links.append(Link(pos, uid))

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
    'display_name' # str or None
))

AUTOFILL = ''
AUTOFILL_SAFETY = '@@'

class CreationStatus:
    """Extra info associated with the de novo creation of a Note."""
    def __init__(self,
                 insufficient_info=False, autofill_failed=False,
                 autofill_unsure=False, unsure_fields=[],
                 autolinked_words={}):
        self.insufficient_info = insufficient_info
        self.autofill_failed = autofill_failed
        self.autofill_unsure = autofill_unsure
        self.unsure_fields = copy.copy(unsure_fields)
        self.autolinked_words = copy.copy(autolinked_words)

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
                self.cstatus.insufficient_info = True
                return

        # try autofill
        self.autofill(vals) # edits cstatus

        # fill into object attributes
        self.fill(vals)

    def __getstate__(self):
        """Get the pickling state."""
        state = {}
        for part in self.parts:
            state[part.name] = getattr(self, part.name)
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
            lt = self.autolink(val)
            setattr(self, part.name, lt)

    def autolink(self, text):
        """Return autolinked LinkedText."""
        lt = LinkedText(text)
        bounds = utils.find_word_boundaries(text)
        for wb in bounds:
            word = text[wb[0]:wb[1]]
            matches = registry.search(word)
            if matches:
                # (JUST TAKES THE FIRST UID MATCHED... FIX THIS?? TODO)
                match_uid = registry.search(word)[0]
                lt.link(Pos(wb[0], wb[1]), match_uid)
                self.cstatus.autolinked_words[word] = str(registry.get(match_uid))
        return lt

    def __str__(self):
        """Convert into the best human-readible identifier of this note."""
        idstr = getattr(self, self.strify[1]).text
        return "{} '{}'".format(self.strify[0], idstr)

class ToolNote(Note):
    """Represents a note about a tool."""
    parts = (
        Part('name', 'Name'),
        Part('cmd', 'Command'),
        Part('ver', 'Version'),
        Part('desc', 'Description'))

    searchable = ('name', 'cmd')
    linked = ('desc',)
    required = ('cmd',)
    unsafe = ('ver',)
    strify = ('Tool', 'name')

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
        Part('shellcmd', 'Shell command'),
        Part('toolcmd', 'Tool'),
        Part('time', 'Time'),
        Part('desc', 'Description'))

    required = ('shellcmd',)
    searchable = tuple()
    linked = ('shellcmd', 'toolcmd', 'desc')
    unsafe = tuple()

    def autofill(self, vals):
        """Attempt to autofill empty values."""
        if vals['toolcmd'] == AUTOFILL:
            vals['toolcmd'] = vals['shellcmd'].split(' ')[0]
        if vals['time'] == AUTOFILL:
            vals['time'] = utils.get_timestamp()

    def __str__(self):
        """Overrides base Note __str__()."""
        s = "Action using '{}' at time '{}'".format(
            self.toolcmd.text, self.time.text)

class DataNote(Note):
    """Represents a note about a data file."""
    parts = (
        Part('name', 'Name'),
        Part('path', 'Path'),
        Part('src', 'Source'), # kind of like a secondary description
        Part('desc', 'Description'))

    searchable = ('name', 'path')
    linked = ('src', 'desc')
    required = ('path',)
    unsafe = tuple()
    strify = ('Data', 'name')

    def autofill(self, vals):
        """Attempt to autofill empty values."""
        if vals['name'] == AUTOFILL:
            vals['name'] = vals['path'].split('/')[-1]
