#!/usr/bin/env python3
"""Run an isolated headless probe until its flushed COMPLETE log, or report timeout."""
import argparse, json, os, subprocess, threading, time
from pathlib import Path

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--dosbox',type=Path,default=Path(os.environ.get('DOSBOX_X','/workspace/shared/dosbox-x/run')),help='DOSBox-X executable (or set DOSBOX_X)');ap.add_argument('config',type=Path);ap.add_argument('guest_log',type=Path);ap.add_argument('--host-log',required=True,type=Path);ap.add_argument('--timeout',type=float,default=120);a=ap.parse_args()
 if a.guest_log.exists():a.guest_log.rename(a.guest_log.with_suffix('.OLD'))
 env=os.environ.copy();env['SDL_VIDEODRIVER']='dummy'
 p=subprocess.Popen([str(a.dosbox.resolve()),'-nopromptfolder','-conf',str(a.config)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env)
 def output():
  kept=0
  with a.host_log.open('wb') as f:
   while True:
    b=p.stdout.read(4096)
    if not b:break
    if kept<1048576:f.write(b[:1048576-kept]);kept+=len(b)
 t=threading.Thread(target=output);t.start();start=time.monotonic();complete=False
 try:
  while time.monotonic()-start<a.timeout:
   if a.guest_log.exists() and 'COMPLETE=1' in a.guest_log.read_text(errors='replace'):
    complete=True;break
   if p.poll() is not None:break
   time.sleep(.2)
 finally:
  if p.poll() is None:p.kill()
  p.wait();t.join(timeout=5)
 print(json.dumps({'complete':complete,'elapsed_seconds':round(time.monotonic()-start,3),'config':str(a.config),'guest_log':str(a.guest_log),'host_log':str(a.host_log)}))
 return int(not complete)
if __name__=='__main__':raise SystemExit(main())
