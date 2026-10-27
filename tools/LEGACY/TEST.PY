from pathlib import Path
import hashlib,importlib.machinery,io,json,tempfile,zipfile
root=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as t:
 folder=Path(t);(folder/'SOURCE.PY').write_bytes((root/'SOURCE.PY').read_bytes());raw=(root/'SOURCES.ZIP').read_bytes();(folder/'SOURCES.ZIP').write_bytes(raw)
 m=importlib.machinery.SourceFileLoader('legacy_test',str(folder/'SOURCE.PY')).load_module()
 def ident(b):return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 def refused(fn):
  try:fn()
  except ValueError:return
  raise AssertionError('Expected refusal')
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  for n in m.NAMES:
   b=z.read(n);assert m.source(n,b'changed',ident(b))==b
 assert m.source('unlisted',b'changed',ident(b'old'))==b'changed'
 refused(lambda:m.source(m.NAMES[0],b'changed',ident(b'wrong pin')))
 (folder/'SOURCES.ZIP').write_bytes(raw+b'tamper')
 refused(lambda:m.source(m.NAMES[0],b'changed',ident(b'old')))
 assert m.source('live',b'valid',ident(b'valid'))==b'valid'
 print('PASS historical source pins, explicit inventory, unknown-path no-fallback, changed-pin refusal, archive tamper refusal and live exact input')
