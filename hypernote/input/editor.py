"""Implement a note input system using a text editor."""
import tempfile
import os
import subprocess
from input.base import Cancelled, Invalid

class Cancelled(RuntimeError):
    pass
class Invalid(RuntimeError):
    pass

def input_note(note_cls, editor):
    """Get note details from user using a text editor.

    note_cls: the class of the note to get.
    editor: the name (str) of the editor to use."""
    text = ('# Fill in details about the note below.\n'
            '# Lines beginning with \'#\' are comments.\n'
            '# To cancel, write \'CANCEL\' on its own line, anywhere in the'
            ' file.\n'
            '# If a field is left blank, HyperNote will try to autofill it.'
            '\n\n')
    dispname_to_name = {}
    for part in note_cls.parts:
        # display_name can be None
        disp_name = part.display_name
        if not disp_name:
            disp_name = part.name
        dispname_to_name[disp_name] = part.name

        if part.name in note_cls.required:
            text += '# REQUIRED\n'
        text += disp_name + ' = \n\n'

    # call the editor
    fd, filename = tempfile.mkstemp()
    os.write(fd, bytes(text, 'utf8'))
    os.close(fd)
    editor_process = subprocess.Popen((editor, filename))
    editor_process.wait()

    # read the file
    with open(filename) as fin:
        inp_text = list(fin.readlines())
    info = {}
    for line in inp_text:
        line = line.strip()
        if not line or line[0] == '#':
            # comment or empty
            continue
        if line in ('CANCEL', 'cancel'):
            # cancelled
            raise Cancelled()
        if line.count('=') != 1:
            # not a valid input line
            print("LINE: '{}'".format(line))
            raise Invalid()
        key, val = line.split('=')
        key, val = key.strip(), val.strip()
        if not val:
            # left empty; autofill
            continue
        info[dispname_to_name[key]] = val

    return info
