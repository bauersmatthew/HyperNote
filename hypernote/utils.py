"""Implement various utilities."""
import subprocess
import time
import datetime
import os.path

def get_process_info(cmd):
    """Get the stdout, stderr, and returnvalue of a command."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(.5)
    if p.poll() is None:
        p.kill()
        return None, None, None
    o, e = p.communicate()
    rv = p.returncode
    return o, e, rv
    
def autodetect_version(cmd):
    """Try to autodetect the version of a command."""
    # try with --version...
    o, e, rv = get_process_info((cmd, '--version'))
    if rv is None or rv != 0:
        # that didn't work, try with -V...
        o, e, rv = get_process_info((cmd, '-V'))
    if rv is None or rv != 0:
        # nothing worked
        return None
    # maybe something worked?; try to extract info from stdout/err
    o = o.decode().split('\n')[0].strip()
    e = e.decode().split('\n')[0].strip()
    src = o
    if not o:
        # o is empty; try e instead
        src = e
        if not e:
            # e is empty; we got nothing
            return None
    first_line = src.split('\n')[0]
    return first_line

def get_timestamp():
    """Get the current timestamp as a string."""
    return str(datetime.datetime.now())

def find_word_boundaries(source):
    """Return a list of tuples containing [start, end) for each word."""
    in_word = False
    bounds = []
    cur_bound_start = None
    whitespace = ' \t\n'
    for i, ch in enumerate(source):
        if not in_word and ch not in whitespace:
            in_word = True
            cur_bound_start = i
        elif in_word and ch in whitespace:
            in_word = False
            bounds.append((cur_bound_start, i))
    if in_word:
        bounds.append((cur_bound_start, len(source)))
    return bounds

def find_registry(base='.'):
    """Find the registry."""
    test_path = os.path.relpath('{}/.hnote'.format(base))
    if os.path.isfile(test_path):
        return test_path
    # .hnote not found; go to parent if not at root already
    if os.path.samefile(base, '/'): # at root; abort
        return None
    return find_registry('{}/..'.format(base))
