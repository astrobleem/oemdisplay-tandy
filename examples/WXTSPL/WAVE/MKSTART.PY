"""Make a fresh PRIVATE startup add-on from the user's exact owned WIN.CNF.
Writes only a new output folder. Never changes installed Windows or WIN.COM.
"""
from pathlib import Path
import argparse,hashlib,json,shutil
HERE=Path(__file__).resolve().parent
CNF_SHA='371bd1935f84505d61873f1e08a17b858d667a5149d71995d4285c6f17782bdb'
def sha(data):return hashlib.sha256(data).hexdigest()
def starter_batch():
 return ('@ECHO OFF\nRESERVE\nIF ERRORLEVEL 1 GOTO BAD\n'
         'SET PATH=C:\\WINDOWS;C:\\WINDOWS\\SYSTEM;Z:\\\n'
         'SET TEMP=C:\\WINDOWS\\TEMP\nCD WINDOWS\nXTCLEAN\n'
         'IF ERRORLEVEL 1 GOTO WINFAIL\nCD \\\n'
         'ECHO Windows returned.\nGOTO DONE\n'
         ':WINFAIL\nECHO Windows startup or cleanup failed; see WRAP.BIN.\n'
         'GOTO DONE\n:BAD\nECHO RESERVE refused; Windows was not started.\n:DONE\n')

def make(windows,out):
 if out.exists():raise ValueError('Choose a new output directory; existing files are preserved')
 policy=json.loads((HERE/'DEFAULT.JSON').read_text())
 data={}
 for name,pin in policy['payload'].items():
  p=HERE/name
  if p.is_symlink() or not p.is_file():raise ValueError('Missing or linked payload: '+name)
  data[name]=p.read_bytes()
  if sha(data[name])!=pin['sha256'] or len(data[name])!=pin['bytes']:raise ValueError('Payload pin mismatch: '+name)
 cnf=(windows/'SYSTEM/WIN.CNF').read_bytes()
 if len(cnf)!=3456 or sha(cnf)!=CNF_SHA:raise ValueError('Unsupported owned WIN.CNF; exact qualified loader required')
 combined=cnf+data['XTLOGO.LGO']
 if sha(combined)!=policy['private_combined_sha256']:raise ValueError('Combined loader differs from native-qualified bytes')
 out.mkdir();(out/'WINDOWS').mkdir()
 (out/'WINDOWS/XTTEST.COM').write_bytes(combined)
 (out/'WINDOWS/XTCLEAN.COM').write_bytes(data['XTCLEAN.COM'])
 (out/'RESERVE.COM').write_bytes(data['RESERVE.COM'])
 start=starter_batch()
 (out/'START.BAT').write_bytes(start.replace('\n','\r\n').encode('ascii'))
 record={'publication_allowed':False,'kind':'private-owned-loader-startup-addon','installed_windows_changed':False,'files':{str(p.relative_to(out)):sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()},'default':'accepted fixed-color slow wave','scope':'C:\\WINDOWS qualified DOS layout; merge add-on into a disposable/user-authorized clone only','qualification_limits':policy['qualification_limits']}
 (out/'PRIVATE.JSON').write_text(json.dumps(record,indent=2));return record
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--windows',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 try:print(json.dumps(make(a.windows,a.out),indent=2))
 except (OSError,ValueError) as e:ap.exit(1,'Refused: '+str(e)+'\n')
