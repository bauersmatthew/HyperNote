"""Implements a registry of note-note relations."""
import pickle

Relation = namedtuple('Relation', ('uidA', 'uidB', 'typeA', 'typeB'))
# uidA, uidB:   uids of the two notes involved in this relation
# typeA, typeB: the type of involvement each note has in this relation
#               e.g. created by, used in, etc.
RT_USED, RT_USED_BY, \
    RT_CREATED, RT_CREATED_BY, \
    RT_BEFORE, RT_AFTER, \
    *_ = range(100)

# database of relations
reldb = []

def load(path):
    """Load the relation registry from file."""
    fin = open(path, 'rb')
    while True:
        try:
            rel = pickle.load(fin)
            add(rel)
        except:
            # eof
            break
    fin.close()

def save(path):
    """Save the relation registry to file."""
    fout = open(path, 'wb')
    for rel in reldb:
        pickle.dump(rel, fout)
    fout.close()

def add(rel):
    """Add a Relation to the database."""
    global reldb
    reldb.append(rel)

def get(query):
    """Query the relation database.

    The query argument is a tuple of UIDs.
    If query contains one value, find all relations pertaining to the given UID.
    If query contains two values, find all relations pertaining to both UIDs.

    Is a generator!
    """
    global reldb
    for rel in reldb:
        if is_match(query, rel):
            yield rel
    
def is_match(query, rel):
    """Decides whether the given query matches the relation."""
    if query[0] in (rel.uidA, rel.uidB):
        if len(query) > 1:
            return query[1] in (rel.uidA, rel.uidB)
        return True
    return False

__all__ = ['Relation', 'load', 'save', 'add', 'get']
