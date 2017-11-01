"""Send a hyperlinked notebook to be viewed through HyperPage."""
from hypernote import registry
from hypernote import note
from tempfile import TemporaryDirectory
import subprocess

TEMP_DIR = None

def run():
    with TemporaryDirectory() as tempdir:
        global TEMP_DIR
        TEMP_DIR = tempdir

        # generate all note pages
        for uid in registry.notes:
            genpage_general(registry.get(uid))

        # generate title page
        action_notes = get_action_notes()
        dump_file(generate_titlepage(action_notes), tempdir+'/home.md')
        subprocess.run(['hpage', tempdir+'/home.md'])

def get_action_notes():
    """Get all action notes from the registry; sort chronologically."""
    return sorted(
        [registry.notes[uid] for uid in registry.notes
         if registry.notes[uid].__class__ == note.ActionNote],
        key=lambda n: n.time)

def homelinked(inner):
    """Wrapper that links the page returned by the inner function home."""
    def fun(n):
        t = inner(n)
        return t + '\n[Return to the homepage.]({}/home.md)\n'.format(TEMP_DIR)
    return fun

def autodump(inner):
    """Wrapper that automatically dumps to file the inner return value."""
    def fun(n):
        t = inner(n)
        dump_file(t, '{}/{}.md'.format(TEMP_DIR, n.uid))
    return fun

def generate_titlepage(notes):
    """Generate a home/landing/title page that links to all the action notes."""
    # header
    text = '{} total actions have been recorded in this notebook.\n\n'.format(
        len(notes))
    # list of links to each action
    for i, n in enumerate(notes):
        text += '{}. [{}]({})\n'.format(
            i+1,
            n.desc.text.split('\n')[0],
            '{}/{}.md'.format(TEMP_DIR, n.uid))
    return text

def genpage_general(any_note):
    """Correctly generate markdown for the given note of any type."""
    f = None
    c = any_note.__class__
    if c == note.ActionNote:
        f = genpage_action
    elif c == note.ToolNote:
        f = genpage_tool
    else:
        f = genpage_data
    return f(any_note)

@autodump
@homelinked
def genpage_action(action_note):
    """Generate markdown for an action note."""
    return ('**{}**\n\n'
            'Performed at: *{}*\n\n'
            '{}\n').format(
                render_links(action_note.shellcmd),
                str(action_note.time),
                render_links(action_note.desc))

@autodump
@homelinked
def genpage_tool(tool_note):
    """Generate markdown for a tool note."""
    return ('**{}**\n\n'
            'Command: *{}*\n\n'
            'Version: {}\n\n'
            '{}\n').format(
                tool_note.name,
                tool_note.cmd,
                tool_note.ver,
                render_links(tool_note.desc))

@autodump
@homelinked
def genpage_data(data_note):
    """Generate markdown for a data note."""
    return ('**{}**\n\n'
            '*{}*\n\n'
            'Source: *{}*\n\n'
            '{}\n').format(
                data_note.name,
                data_note.path,
                render_links(data_note.src),
                render_links(data_note.desc))

def render_links(ltext):
    """Convert a LinkedText object into markdown."""
    text = ''
    last_link = None
    for link in ltext:
        last_end = last_link.pos.end if last_link is not None else 0
        # add in plaintext between last link and this one
        text += ltext.text[last_end:link.pos.start]
        # add in link text
        text += '[{}]({})'.format(ltext[link.pos],
                                  '{}/{}.md'.format(TEMP_DIR, link.dest))
        last_link = link
    # add in plaintext between last link and end of string
    last_end = last_link.pos.end if last_link is not None else 0
    text += ltext.text[last_end:]
    return text

def dump_file(text, path):
    """Dump the given text to the file at the given path."""
    with open(path, 'w') as fout:
        fout.write(text)
