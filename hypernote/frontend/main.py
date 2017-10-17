"""The main command line interface for the program."""
import sys
import os.path
from hypernote.input.editor import input_note
from hypernote import note
from hypernote import registry

def main():
    """Entry point; handles exceptions thrown by main_internal()."""
    try:
        main_internal()
    except RuntimeError as err:
        sys.stderr.write(str(err) + '\n')
        return -1
    return 0

def main_internal():
    """Main routine but throws exceptions."""
    sys.argv = sys.argv[1:]
    if len(sys.argv) < 1:
        raise RuntimeError("No command given! Type 'hnote help' for help.")
    command = 'public_cmd_' + sys.argv[0]
    if command not in globals():
        raise RuntimeError(
            "Command '{}' not recognized! Type 'hnote help' for help.")
    # pass rest of args down to subcommand
    globals()[command](sys.argv[1:])

def find_registry(base='.'):
    """Find the registry."""
    test_path = os.path.relpath('{}/.hnote'.format(base))
    if os.path.isdir(test_path):
        return test_path
    # .hnote not found; go to parent if not at root already
    if os.path.samefile(base, '/'): # at root; abort
        return None
    return '{}/..'.format(base)

def use_reg(inner):
    """Wrapper for functions that need to load the registry."""
    path = find_registry()
    def fun(args):
        registry.load(path)
        inner(args)
        registry.save(path)
    return fun

def confirm_note(new_note):
    """Confirm with the user that the note information is correct."""
    if not new_note.cstatus.unsure_fields:
        return True
    dispnames = {p[0] : p[1] for p in new_note.parts}
    w = sys.stdout.write
    w('Please confirm that the following fields have been autofilled '
      'correctly:\n')
    for field in new_note.cstatus.unsure_fields:
        w('{}: {}\n'.format(dispnames[field], getattr(new_note, field).text))
    w('Correct? [y/] ')
    if input().lower().strip() not in ('y', 'yes'):
        return False
    return True

def public_cmd_help(args):
    """help
    Print a help message."""
    # collect commands
    cmds = {}
    for token in globals():
        if 'public_cmd_' in token:
            name = '_'.join(token.split('_')[2:])
            cmds[name] = globals()[token].__doc__

    msg = 'hnote <cmd> [args...]\nCommands:\n\n'
    for cmd in cmds:
        if cmds[cmd].__doc__ is not None:
            desc_lines = [l.strip() for l in cmds[cmd].split('\n')]
            msg += '\n'.join(desc_lines)
        msg += '\n\n'

    sys.stdout.write(msg)

def parse_prefilled_standard(args, trans):
    """Parse command line args to get prefill options."""
    prefilled = {}
    for arg in args:
        if len(arg) < 3 or arg[0] != '-' or arg[1] not in trans:
            raise RuntimeError("Invalid argument: '{}'".format(arg))
        prefilled[trans[arg[1]]] = arg[2:]
    return prefilled

def create_note_standard(note_type, vals):
    """Create and register a new note; handle the creation Signal."""
    new_note = None
    try:
        new_note = note_type(registry.gen_uid(), vals)
    except note.CreationFailure as cfail:
        raise RuntimeError(str(cfail.status))
    if new_note.cstatus.autofill_unsure and not confirm_note(new_note):
        raise RuntimeError('Note creation cancelled by user.')
    registry.add(new_note)

def standard_note_registration_command(docstr, note_type, trans):
    """Create a standard note registration command function."""
    @use_reg
    def fun(args):
        prefilled = parse_prefilled_standard(args, trans)
        vals = input_note(note_type, prefilled)
        create_note_standard(note_type, vals)
    fun.__doc__ = docstr
    return fun
    
public_cmd_data = standard_note_registration_command(
    """data [-n"name"] [-p"path"] [-s"source"] [-d"description"]
    Record information about a data file.""",
    note.DataNote,
    dict(n='name', p='path', s='src', d='desc'))

public_cmd_tool = standard_note_registration_command(
    """tool [-n"name"] [-c"command"] [-v"version"] [-d"description"]
    Record information about a tool.""",
    note.ToolNote,
    dict(n='name', c='cmd', v='ver', d='desc'))

public_cmd_action = standard_note_registration_command(
    """action -s"shell command" [-t"tool"] [-w"time"] [-d"description"]
    Record a shell command. (Do not run it.)""",
    note.ActionNote,
    dict(s='shellcmd', t='toolcmd', w='time', d='desc'))

@use_reg
def public_cmd_run(args):
    """run -s"shell command" [-t"tool"] [-w"time"] [-d"description"]
    Run and record a shell command."""
    public_cmd_action(args)
    # run the command...
    # (TODO)

def public_cmd_init(args):
    """init
    Create an (empty) notebook in this directory."""
    registry.save('./.hnote')

if __name__ == '__main__':
    main()
