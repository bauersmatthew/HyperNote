"""Implement a note input system using a text editor."""
import tempfile
import os
import subprocess
from hypernote.input.base import Cancelled, Invalid

def input_note(note_cls, prefilled={}, editor='vim'):
    """Get note details from user using a text editor.

    note_cls: the class of the note to get.
    editor: the name (str) of the editor to use."""
    text = ('# Fill in details about the note below.\n'
            '# To cancel, write \'CANCEL\' on its own line, anywhere in the'
            ' file.\n'
            '# Lines beginning with \'#\' are comments.\n'
            '# Lines beginning with \'$\' mark the beginning of a field;'
            ' the field includes all the text after the \'=\' and before the'
            ' next field or the end of the file.\n'
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
        if part.name in note_cls.unsafe:
            text += "# MAY BE UNSAFE TO AUTOFILL; TYPE '@@' TO AUTOFILL.\n"
        text += '$ {} = '.format(disp_name)
        if part.name in prefilled:
            text += prefilled[part.name]
        text += '\n\n'

    # call the editor
    fd, filename = tempfile.mkstemp()
    os.write(fd, bytes(text, 'utf8'))
    os.close(fd)
    editor_process = subprocess.Popen((editor, filename))
    editor_process.wait()

    # read the file
    inp_text = None
    with open(filename) as fin:
        inp_text = list(fin.readlines())
    info = {}
    cur_field = None
    cur_field_lines = []
    for line in inp_text:
        app_text = ''
        line = line.strip()
        if line == 'CANCEL':
            # CANCEL on cancel lines
            raise Cancelled()
        elif line and line[0] == '#':
            # IGNORE comment lines
            continue
        elif line and line[0] == '$' and line.count('=') >= 1:
            # STORE on field-start lines
            if cur_field is not None:
                # remove blank lines before and after (but not in the middle)
                info[cur_field] = '\n'.join(cur_field_lines).strip('\n')
            # extract new cur_field
            new_cf_dispname = line[1:line.find('=')].strip()
            if new_cf_dispname not in dispname_to_name:
                raise Invalid()
            cur_field = dispname_to_name[new_cf_dispname]
            # extract first line
            cur_field_lines = [line[line.find('=')+1:].strip()]
        else:
            # KEEP all other lines (including blank lines!)
            cur_field_lines.append(line)
    # STORE final field
    if cur_field is not None:
        # remove blank lines before and after (but not in the middle)
        info[cur_field] = '\n'.join(cur_field_lines).strip('\n')
               
    return info
