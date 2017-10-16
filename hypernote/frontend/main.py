"""The main command line interface for the program."""
import sys
from import.editor import input_note
import note
import registry

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

def find_registry():
    """Find the registry."""
    return ''

def use_reg(inner):
    """Wrapper for functions that need to load the registry."""
    path = find_registry()
    def fun(args):
        registry.load(path)
        inner(args)
        registry.save(path)
    return fun

def confirm_note(note):
    """Confirm with the user that the note information is correct."""
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
        desc_lines = [l.strip() for l in cmds[cmd].__doc__.split('\n')]
        msg.append('\n'.join(desc_lines))
        msg.append('\n\n')

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
    try:
        new_note = note_type(registry.gen_uid(), vals)
    except note.Signal as signal:
        if not signal.is_ok():
            raise Runtimeerror(str(signal))
        if signal.has(note.FSF_AUTOFILL_UNSURE):
            confirm_note(new_note)
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
