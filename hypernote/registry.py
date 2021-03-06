"""Implements a searchable registry of notes."""
from collections import namedtuple
import regex
import pickle
import random
from hypernote import fileio

# one entry in the search table
STEntry = namedtuple('STEntry', ('text', 'uid'))
search_table = []

# uid -> note
notes = {}

def gen_uid_possibility():
    """Generate a possible ID (unchecked)."""
    return random.getrandbits(31) # 31 bits because we save as SIGNED
    
def gen_uid():
    """Generate a new UID, assuming that the registry is loaded."""
    uid = gen_uid_possibility()
    while uid in notes:
        uid = gen_uid_possibility()
    return uid

def load(path):
    """Load the registry from file."""
    if path is None:
        return
    data_all = None
    with open(path, 'rb') as fin:
        data_all = bytearray(fin.read())
    while data_all:
        note = fileio.load_object(data_all)
        add(note)

def save(path):
    """Save the registry to file."""
    if path is None:
        return
    global notes
    with open(path, 'wb') as fout:
        for uid in notes:
            note = notes[uid]
            enc = fileio.get_encoder(type(note))
            data = enc(note)
            fout.write(data)

def add(note):
    """Add a note to the registry.

    If another note already exists with one or more identical searchables,
    raise a RuntimeError."""
    global notes, search_table

    # check that a note doesn't already exist with these
    # searchable properties
    for attr in note.searchable:
        query = str(getattr(note, attr))
        if search(query):
            raise RuntimeError('Another note already exists with a searchable'
                               " property of '{}'.".format(query))

    # "register" note
    notes[note.uid] = note

    # register search terms
    for attr in note.searchable:
        entry = STEntry(str(getattr(note, attr)), note.uid)
        search_table.append(entry)

def get(uid):
    """Get the note identifed by the given UID."""
    global notes
    return notes[uid]

def search(query):
    """Identify matches between the plaintext query and note UIDs.

    Return a list of matching UIDs."""
    global search_table
    matches = [e for e in search_table if e.text.lower() == query.lower()]
    matches_unique_uids = []
    for m in matches:
        if m.uid not in matches_unique_uids:
            matches_unique_uids.append(m.uid)
    return matches_unique_uids

def search_depr(query):
    """Identify matches between the plaintext query and note UIDs.

    Return a list of up to five best-matching UIDs.
    Deprecated!"""
    global search_table
    # find the top 5 matches?
    Match = namedtuple('Match', 'uid', 'score')
    matches = [] # sorted in order of decreasing score
    for entry in search_table:
        score = match(query, entry.text)
        # this alg is not incredible
        matches.append((entry.uid, score))
        matches.sort(key=lambda x: x.score, reverse=True)
        if len(matches) > 5:
            del matches[5] # chop off the end
    match_uids = [m.uid for m in matches]
    return match_uids

def match(query, source):
    """Return the 'match score' between the given query and source strings."""
    # count total length of query contigs found in source
    score = 0
    minlen = max([3, len(source)//3])
    for contig in contigs(query, minlen):
        escaped = escape_regex(contig)
        # FOOD FOR THOUGHT: does the number found matter here?
        num_found = len(regex.findall(escaped, source))
        score += num_found*len(contig)
    return score/len(source)

def contigs(s, minlen=1):
    """Generate all 'contigs' in the given string at least minlen long.

    Starts from the identity contig; shortens from the end before moving
    the start position up."""
    for c_spos in range(len(s)):
        for c_len in reversed(range(minlen, len(s)-c_spos+1)):
            yield s[c_spos:c_spos+c_len]

def escape_regex(s):
    """Escape the given string for regex."""
    ret = ''
    specials = '.^$*+?{}[]|()\\'
    for ch in s:
        if ch in specials:
            ret += '\\' # escape it
        ret += ch
    return ret
