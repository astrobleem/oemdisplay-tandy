"""Run prepared private DOS fixtures only after obtaining the coordinated slot."""
from pathlib import Path
import argparse,fcntl,importlib.machinery,os,signal,subprocess
HERE=Path(__file__).resolve().parent
I=importlib.machinery.SourceFileLoader('font_install_cases',str(HERE/'INSTALL.PY')).load_module()
def active():
 lines=subprocess.check_output(['ps','-eo','stat=,comm='],text=True).splitlines()
 return [x for x in lines if x.split()[-1].lower() in ('dosbox-x','dosbox','86box','pcem','tandybox') and not x.lstrip().startswith('Z')]
def run(fixtures,emulator,lease,cases,seconds):
 assert fixtures.is_dir() and emulator.is_file() and lease.is_absolute()
 with lease.open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  assert not active(),'Another emulator is active; coordinated slot is unavailable'
  for case in cases:
   assert case in I.CASES,case
   folder=fixtures/case;conf=folder/'RUN.CNF';text=conf.read_text()
   assert 'memsizekb=640' in text and 'cputype=8086_prefetch' in text and 'xms=false' in text and 'ems=false' in text and 'umb=false' in text
   assert 'mount C "'+str(folder/'guest')+'"' in text,'Fixture must use its own private guest'
   with (folder/'HOST.LOG').open('wb') as log:
    child=subprocess.Popen([str(emulator),'-conf',str(conf)],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    try:
     status=child.wait(timeout=seconds);assert status==0,(case,status)
    finally:
     if child.poll() is None:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=10)
   assert not active(),'Owned emulator did not release the slot'
   done=folder/'guest/DONE.TXT'
   assert done.exists() and done.read_text().strip()=='PASS',case+' failed; retain guest/logs'
   print(case,'native script PASS',flush=True)
 print('All requested native scripts completed; owned processes stopped and shared lease released.')
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__)
 for n in ('fixtures','emulator','lease'):a.add_argument('--'+n,type=Path,required=True)
 a.add_argument('--cases',nargs='+',default=I.CASES,choices=I.CASES);a.add_argument('--timeout',type=int,default=240);v=a.parse_args();run(v.fixtures.resolve(),v.emulator.resolve(),v.lease.resolve(),v.cases,v.timeout)
