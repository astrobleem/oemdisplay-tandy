"""Require an exact completed DISPLAY installation before the full repair."""
from pathlib import Path
import importlib.machinery,unittest
M=importlib.machinery.SourceFileLoader('setup_checkpoint',str(Path(__file__).with_name('CHECKSET.PY'))).load_module()
class Files:
 def __init__(self):
  self.data={'DISPOK.TXT':b'DISPLAY_FINISHED\r\n','DISPLAY.LOG':b'Windows Setup returned status 0.\r\nThe selected HPXY driver already matches; no replacement needed.\r\n','WINDOWS/SYSTEM/HPXY.DRV':b'candidate','WINDOWS/SYSTEM.INI':b'[boot]\r\ndisplay.drv=HPXY.DRV\r\n'}
 def readbytes(self,n):return self.data[n]
 def exists(self,n):return n in self.data
class Checkpoint(unittest.TestCase):
 def setUp(self):self.fs=Files()
 def reject(self):
  with self.assertRaises((AssertionError,KeyError)):M.setup_evidence(self.fs,b'candidate')
 def test_positive_control(self):self.assertEqual(M.setup_evidence(self.fs,b'candidate')[1],b'candidate')
 def test_unknown_setup_status(self):self.fs.data['DISPLAY.LOG']=self.fs.data['DISPLAY.LOG'].replace(b'status 0',b'status 2');self.reject()
 def test_setup_not_launched(self):self.fs.data['DISPLAY.LOG']=self.fs.data['DISPLAY.LOG'].replace(b'status 0',b'status -1');self.reject()
 def test_declined_replacement(self):self.fs.data['DISPLAY.LOG']=b'Windows Setup returned status 1.\r\nNo replacement requested.\r\n';self.reject()
 def test_unfinished_helper_replacement(self):self.fs.data['DISPLAY.LOG']=b'Windows Setup returned status 1.\r\nReplace only SYSTEM\\HPXY.DRV from this source? [y/N] Y\r\n';self.reject()
 def test_documented_status1_helper_replacement(self):
  self.fs.data['DISPLAY.LOG']=b'Windows Setup returned status 1.\r\nReplace only SYSTEM\\HPXY.DRV from this source? [y/N] HPXY updated. Other installed files and INI settings were not repaired.\r\n'
  self.assertEqual(M.setup_evidence(self.fs,b'candidate')[3:],(1,True))
 def test_old_driver(self):self.fs.data['WINDOWS/SYSTEM/HPXY.DRV']=b'released';self.reject()
 def test_wrong_display_selection(self):self.fs.data['WINDOWS/SYSTEM.INI']=b'display.drv=CGA.DRV\r\n';self.reject()
 def test_after_repair_return(self):self.fs.data['RETURN1.TXT']=b'RETURNED';self.reject()
 def test_missing_completion_marker(self):del self.fs.data['DISPOK.TXT'];self.reject()
 def test_missing_no_replacement_confirmation(self):self.fs.data['DISPLAY.LOG']=b'Windows Setup returned status 0.\r\n';self.reject()
if __name__=='__main__':unittest.main()
