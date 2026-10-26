"""Native rc.8 archive closure and qualification-gate regression checks."""
import copy
import importlib.machinery
import json
import io
import shutil
import zipfile
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

M = importlib.machinery.SourceFileLoader("native_rc8_publish", str(Path(__file__).with_name("RCPUB.PY"))).load_module()
COMMIT = "0123456789abcdef0123456789abcdef01234567"

class NativePublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.entries = M.collect()
        self.archive = M.pub.zip_bytes(self.entries)
        self.qual = {"status": "PASS_NATIVE_AND_HOST", "physical_test": False,
                     "public_assets": {"WINXT.ZIP": M.pub.identity(self.archive),
                     "WINXT.EXE": M.pub.identity(self.entries["PREPXR.EXE"] + self.archive)},
                     "cold": {"complete": True, "owned_stopped": True, "lease_released": True}}
        for mode, count in (("fresh", 369), ("update", 82)):
            self.qual[mode] = {"complete": True, "owned_stopped": True, "lease_released": True,
                              "prepared_comparison": {"count": count, "different": []}}
        self.qual["input_validation"] = {
            "helper": M.pub.identity(self.entries["PREPXR.EXE"]),
            "native_corruption": copy.deepcopy(self.qual["cold"]),
            "native_valid_inputs": copy.deepcopy(self.qual["fresh"])}
        self.receipt = self.root / "docs/QUAL/DOSINST/RC8.JSN"
        self.receipt.parent.mkdir(parents=True)

    def run_build(self, output, verify=False):
        self.receipt.write_text(json.dumps(self.qual), encoding="ascii")
        with patch.object(M, "REPO", self.root), patch.object(M, "collect", return_value=self.entries):
            return M.qualified_core(self.entries)

    def test_closed_native_archive(self):
        self.assertEqual(len(self.entries), 57)
        self.assertFalse(any(n.endswith(".PY") for n in self.entries))
        self.assertEqual(M.pub.identity(self.entries["PAYLOAD/CGA.GR2"]), {"bytes": 2104, "sha256": "1fc24254a1b76c2030a0ae60e25a17d6df4730c2a99d293ca22886059d8be067"})
        M.pub.check_zip(self.archive, self.entries, "native")
        self.assertEqual(self.archive, M.pub.zip_bytes(self.entries))

    def test_current_grabber_has_no_loose_root_dependency(self):
        spec = json.loads((M.HERE / "RCPUBLIC.JSN").read_bytes())
        self.assertEqual(spec["files"]["PAYLOAD/CGA.GR2"], {
            "source": "distributions/WINXT/CGA.GR2",
            "identity": M.pub.identity(self.entries["PAYLOAD/CGA.GR2"])})
        original = M.pub.read_file
        def read_without_loose_root(root, name):
            self.assertNotEqual(str(name), "CGA.GR2")
            return original(root, name)
        with patch.object(M.pub, "read_file", side_effect=read_without_loose_root):
            self.assertEqual(M.collect(), self.entries)

    def test_recipe_uses_bundled_grabber_for_both_output_trees(self):
        import re
        rows = re.findall(r'\{"([^"\n]+)","([^"\n]+)",(\d+)UL,(\d+)\}',
                          (M.HERE / "XRFILES.H").read_text())
        grabbers = [(path, source, int(size), int(kind))
                    for path, source, size, kind in rows if source == "CGA.GR2"]
        self.assertEqual(len(grabbers), 3)
        self.assertTrue(all(size == 2104 and kind == 0 for _, _, size, kind in grabbers))
        for _, source, size, _ in grabbers:
            self.assertEqual(len(self.entries["PAYLOAD/" + source]), size)

    def test_windows_crc_inventory_matches_qualified_inputs(self):
        recipe = (M.HERE / "XRFILES.H").read_text()
        header = (M.HERE / "XRINPUT.H").read_text()
        pins = json.loads((M.HERE / "XRINPUT.JSN").read_bytes())
        qualified = {r["path"]: r for r in json.loads((M.HERE.parent / "XR1PACK/INPUTS.JSN").read_bytes())["files"]}
        self.assertEqual(len(pins), 284)
        M.check_inputs(recipe, header, pins, qualified)
        changed = copy.deepcopy(pins)
        changed["W30/123.PIF"]["crc32"] = "00000000"
        with self.assertRaises(ValueError):
            M.check_inputs(recipe, header, changed, qualified)
        changed = copy.deepcopy(pins)
        changed["W30/123.PIF"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            M.check_inputs(recipe, header, changed, qualified)
        with self.assertRaises(ValueError):
            M.check_inputs(recipe, header.replace("W30\\\\123.PIF", "wrong", 1), pins, qualified)

    def test_update_after_winamp_needs_no_original_stock_sound(self):
        import re
        rows = re.findall(r'\{"([^"\n]+)","([^"\n]+)",(\d+)UL,(\d+)\}',
                          (M.HERE / "XRFILES.H").read_text())
        owned = [row for row in rows if row[3] == "1"]
        self.assertEqual(len(owned), 284)
        self.assertTrue(all(row[0].startswith("W30\\\\") for row in owned))
        update = [row for row in rows if not row[0].startswith("W30\\\\")]
        self.assertEqual(len(update), 82)
        self.assertFalse(any(row[3] == "1" for row in update))
        sound = [row for row in update if row[1] == "SOUND.DRV"]
        self.assertEqual(len(sound), 2)
        self.assertTrue(all(row[3] == "0" for row in sound))
        self.assertEqual({row[0] for row in sound},
                         {"WINXT\\\\SOUND.DRV", "WINXT\\\\FILES\\\\SOUND.DRV"})
        source = (M.HERE / "XRPREP.C").read_text()
        self.assertIn('if(fresh||strncmp(files[i].path,"W30\\\\",4))', source)

    def test_preserves_all_284_published_os_identity_rows(self):
        protected = json.loads((M.HERE/'SOUNDDELTA.JSN').read_bytes())['protected']
        for name in ('DOSCORE.H','CRCFAST.H','VARSET.H','XRSTRM.H','XRINPUT.JSN'):
            self.assertEqual(M.pub.identity((M.HERE/name).read_bytes()), protected[name])

    def test_published_fresh_receipt_cannot_qualify_new_helper(self):
        self.qual['fresh']['prepared_comparison']['count'] = 367
        with self.assertRaisesRegex(ValueError, 'Prepared bytes differ: fresh'):
            self.run_build(self.root/'stale-fresh')

    def test_wrong_or_incomplete_native_result_refused_before_output(self):
        original = copy.deepcopy(self.qual)
        for mutate in (lambda q: q["fresh"].update(complete=False),
                       lambda q: q["fresh"].update(error="Setup did not finish"),
                       lambda q: q["update"].update(lease_released=False),
                       lambda q: q["cold"].update(owned_stopped=False),
                       lambda q: q["update"]["prepared_comparison"].update(different=["WINXT/HPXY.DRV"]),
                       lambda q: q["fresh"]["prepared_comparison"].update(count=366),
                       lambda q: q["input_validation"]["helper"].update(sha256="0" * 64),
                       lambda q: q["input_validation"]["native_corruption"].update(complete=False),
                       lambda q: q["input_validation"]["native_valid_inputs"].update(error="CRC did not finish")):
            self.qual = copy.deepcopy(original)
            mutate(self.qual)
            output = self.root / "refused"
            with self.assertRaises(ValueError):
                self.run_build(output)
            self.assertFalse(output.exists())

    def test_changed_qualified_container_refused(self):
        self.qual["public_assets"]["WINXT.ZIP"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.run_build(self.root / "bad")


class ExpandedPublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.entries = M.expanded_entries()
        self.archive = M.pub.zip_bytes(self.entries)
        self.source = M.pub.read_file(M.REPO, "tools/XR1PACK/SOUNDSRC.ZIP")
        self.qual = {"status": "PASS_EXPANDED_NATIVE", "physical_test": False,
                     "archive": M.pub.identity(self.archive),
                     "files": {n: M.pub.identity(b) for n,b in sorted(self.entries.items())},
                     "negative": {"complete": True, "owned_stopped": True, "lease_released": True, "helper": M.pub.identity(self.entries["SETUP.EXE"]), "archive": M.pub.identity(self.archive)}}
        for mode in ("fresh", "update", "drivers_only"):
            self.qual[mode] = {"complete": True, "owned_stopped": True, "lease_released": True,
                               "archive": self.qual["archive"]}
            if mode != "drivers_only":
                self.qual[mode].update(helper=M.pub.identity(self.entries["SETUP.EXE"]),
                    prepared_comparison={"count":375 if mode=="fresh" else 87,"different":[]})
        self.qual["drivers_only"].update(custom_setup_executed=False,
           descriptor_unchanged=True,alternate_source="C:\\EXTRACT\\WINXT")
        self.receipt = self.root / "docs/QUAL/DOSINST/EXPAND.JSN"
        self.receipt.parent.mkdir(parents=True)
        self.qual["evidence"] = {}
        for name in ("EXUP.LOG", "EXUP.PNG", "EXMISS.LOG", "EXBAD.LOG", "EXBAD.PNG", "EXCASE.JSN", "EXFRESH.LOG", "EXFRESH.PNG"):
            data = ("test evidence " + name).encode()
            self.receipt.with_name(name).write_bytes(data)
            self.qual["evidence"][name] = M.pub.identity(data)
        src = self.root / "tools/XR1PACK/SOUNDSRC.ZIP"
        src.parent.mkdir(parents=True);src.write_bytes(self.source)
        self.here = self.root / "tools/DOSINST"
        self.here.mkdir()
        oem_root = self.root / "tools/XROEM"
        shutil.copytree(M.HERE.parent / "XROEM/QA", oem_root / "QA")
        oem = json.loads((M.HERE.parent / "XROEM/NATIVE.JSN").read_bytes())
        oem["packet"] = self.qual["archive"]
        oem["members"] = self.qual["files"]
        oem["sources"] = {n: M.pub.identity(self.entries['WINXT/' + n])
                          for n in oem["sources"]}
        (oem_root / "NATIVE.JSN").write_text(json.dumps(oem))

    def run_build(self, out, verify=False):
        self.receipt.write_text(json.dumps(self.qual), encoding="ascii")
        with patch.object(M,"REPO",self.root),patch.object(M,"HERE",self.here),patch.object(M,"expanded_entries",return_value=self.entries):
            return M.build(out,COMMIT,verify)

    def test_actual_expanded_tree_and_plain_executable(self):
        import struct
        self.assertEqual({n.split('/')[0] for n in self.entries},{"SETUP.EXE","README.TXT","WINXT"})
        self.assertEqual(len(self.entries),62)
        self.assertFalse(any(n.endswith((".ZIP",".PY")) for n in self.entries))
        exe=self.entries['SETUP.EXE'];last,pages=struct.unpack_from('<HH',exe,2)
        self.assertEqual(len(exe),pages*512-(512-last if last else 0))
        self.assertLess(len(exe),90000)
        core=M.collect()
        current=importlib.machinery.SourceFileLoader('test_current_settings',str(M.HERE/'PANUI.PY')).load_module()
        core.update({'PAYLOAD/'+n:b for n,b in current.runtimes().items()})
        for n,b in core.items():
            if n.startswith('PAYLOAD/'):
                self.assertEqual(self.entries['WINXT/'+('HPXY.INF' if n[8:]=='OEMSETUP.INF' else n[8:])],b)
        for n in ('OEMSETUP.INF','CGA.GR2','TANDYGR.GR2','TGCLIP.EXE','HPXY.DRV','XTCSYS.FON','XTCFIX.FON','XTCOEM.FON','XTSTATIC.LGO','WXTSPL01.RLE','DISPLAY.BAT','DISPWIN.BAT'):
            self.assertIn('WINXT/'+n,self.entries)
        M.pub.check_zip(self.archive,self.entries,'expanded')

    def test_expanded_crc_indices_preserve_every_original_windows_identity(self):
        import re
        rows=re.findall(r'{"([^"\n]+)","([^"\n]+)",(\d+)UL,(\d+)}',(M.HERE/'SETFILES.H').read_text())
        crcs=re.findall(r'0x([0-9a-f]{8})UL, /\* ([^*]+) \*/',(M.HERE/'SETINPUT.H').read_text())
        expected=json.loads((M.HERE/'XRINPUT.JSN').read_bytes())
        self.assertEqual(len(rows),375)
        self.assertEqual(len(crcs),375)
        actual={}
        for (path,source,size,kind),(crc,label) in zip(rows,crcs):
            self.assertEqual(path,label)
            if kind=='1':actual[path.replace(chr(92)*2,'/')]=(int(size),crc)
            else:self.assertEqual(crc,'00000000')
        self.assertEqual(actual,{p:(v['bytes'],v['crc32']) for p,v in expected.items()})
        self.assertEqual(len(actual),284)

    def test_verified_current_assets_and_developer_source_separation(self):
        out=self.root/'release';first=self.run_build(out)
        self.assertEqual(first,self.run_build(out,True))
        self.assertEqual(set(first),set(M.ASSETS))
        self.assertEqual((out/'WINXTSRC.ZIP').read_bytes(),self.source)
        self.assertEqual(json.loads((out/'WINXT.JSN').read_bytes())['tag'],'windows-xt')
        with zipfile.ZipFile(io.BytesIO((out/'WINXT.ZIP').read_bytes())) as z:
            self.assertEqual(z.read('SETUP.EXE'),self.entries['SETUP.EXE'])
            self.assertIsNone(z.testzip())
            self.assertNotIn('WINXT.EXE',z.namelist())

    def test_stale_or_incomplete_native_evidence_is_refused(self):
        original=copy.deepcopy(self.qual)
        mutations=[lambda q:q.update(status='PENDING'),lambda q:q['archive'].update(sha256='0'*64),
          lambda q:q['files'].pop('WINXT/HPXY.DRV'),lambda q:q['fresh'].update(complete=False),
          lambda q:q['fresh']['helper'].update(sha256='0'*64),
          lambda q:q['update']['prepared_comparison'].update(count=80),
          lambda q:q['drivers_only'].update(error='copy source prompt'),
          lambda q:q['drivers_only'].update(lease_released=False),lambda q:q['negative'].update(complete=False),
          lambda q:q['drivers_only'].update(custom_setup_executed=True),
          lambda q:q['drivers_only'].update(descriptor_unchanged=False),
          lambda q:q['drivers_only'].update(alternate_source=r'C:\WINXT')]
        for mutate in mutations:
            self.qual=copy.deepcopy(original);mutate(self.qual)
            with self.assertRaises(ValueError):self.run_build(self.root/'refused')
            self.assertFalse((self.root/'refused').exists())

    def test_changed_native_raw_evidence_refused_before_publication(self):
        self.receipt.with_name("EXUP.PNG").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError,"Expanded evidence differs"):
            self.run_build(self.root/"refused")
        self.assertFalse((self.root/"refused").exists())

    def test_modified_asset_extra_file_and_changed_member_refused(self):
        out=self.root/'release';self.run_build(out)
        (out/'extra').write_bytes(b'extra')
        with self.assertRaises(ValueError):self.run_build(out,True)
        (out/'extra').unlink()
        original=(out/'WINXT.ZIP').read_bytes()
        for n in ('SETUP.EXE','WINXT/HPXY.DRV','README.TXT'):
            e=dict(self.entries);e[n]+=b'changed';(out/'WINXT.ZIP').write_bytes(M.pub.zip_bytes(e))
            with self.assertRaises(ValueError):self.run_build(out,True)
        (out/'WINXT.ZIP').write_bytes(original+b'changed')
        with self.assertRaises(ValueError):self.run_build(out,True)

if __name__ == "__main__":
    unittest.main()
