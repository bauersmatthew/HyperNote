"""Implement various utilities."""
import subprocess
import time

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
    """Get the current timestamp as given by the date utility."""
    p = subprocess.Popen('date', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o, e = p.communicate()
    return o.decode().strip()
