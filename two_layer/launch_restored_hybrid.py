#!/usr/bin/python3
"""SSH-safe SIGHUP-immune route launch or event-driven completion wait."""
from pathlib import Path
import os, select, signal, subprocess, sys
ROOT=Path(__file__).resolve().parent
PID=ROOT/'restored_hybrid_route.pid'
def main():
    signal.signal(signal.SIGHUP,signal.SIG_IGN)
    if len(sys.argv)>1 and sys.argv[1]=='wait':
        pid=int(PID.read_text());fd=os.pidfd_open(pid)
        try:
            poll=select.poll();poll.register(fd,select.POLLIN)
            events=poll.poll(540000)
            print('completed' if events else 'still-running',pid,flush=True)
        finally:os.close(fd)
        return
    if PID.exists():
        old=int(PID.read_text())
        try:os.kill(old,0)
        except ProcessLookupError:pass
        else:raise RuntimeError('Existing restored hybrid owner still running')
    log=(ROOT/'restored_hybrid_route.log').open('ab',buffering=0)
    child=subprocess.Popen(['/usr/bin/python3','-u',str(ROOT/'restored_hybrid_route.py')],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    PID.write_text(str(child.pid)+'\n');print('started',child.pid,flush=True)
if __name__=='__main__':main()
