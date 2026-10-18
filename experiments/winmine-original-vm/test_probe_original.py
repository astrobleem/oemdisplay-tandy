import hashlib
import unittest
from unittest.mock import patch

from ne_loader import ImportTarget, LoadedNE, NELoader
from probe_original import run_probe


class ProbeOriginalTests(unittest.TestCase):
    def test_entry_probe_matches_independent_trace_and_keeps_input_unchanged(self):
        memory = bytearray(1 << 20)
        selector, ss = 0x1000, 0x2000
        start = (selector << 4) + 0x0100
        memory[start:start + 12] = bytes.fromhex(
            "31 ED 55 9A 01 00 01 F0 09 C0 74 00"
        )
        image = LoadedNE(
            memory=memory,
            image=object(),
            segment_selectors={1: selector, 2: ss},
            import_targets={(0xF001, 1): ImportTarget("KERNEL", "ordinal", None, 91)},
            initial_cs=selector,
            initial_ip=0x0100,
            initial_ss=ss,
            initial_sp=0,
            loaded_bytes=12,
        )
        original = b"public synthetic test image"
        loader = NELoader(object())
        with patch.object(NELoader, "from_bytes", return_value=loader) as from_bytes:
            with patch.object(loader, "load", return_value=image):
                result = run_probe(original, hashlib.sha256(original).hexdigest())
        from_bytes.assert_called_once_with(original, "WINMINE-original.EXE")
        self.assertTrue(result["reference_match"])
        self.assertTrue(result["input_bytes_unchanged"])
        self.assertEqual(result["import"], {"module": "KERNEL", "kind": "ordinal",
                                               "ordinal": 91, "name": None})
        self.assertEqual(result["host_service"], "KERNEL ordinal 91 InitTask register-return subset")
        self.assertEqual(result["guest_return"], {
            "CS": "1000", "IP": "010C", "post_import_instructions": 2,
            "success_branch_taken": False,
        })
        self.assertEqual(result["final"]["IP"], "010C")
        self.assertEqual(result["final"]["SP"], "FFFC")
        self.assertEqual(result["final"]["AX"], "0001")
        self.assertEqual(result["final"]["BX"], "0080")
        self.assertEqual(result["final"]["CX"], "2000")
        self.assertEqual(result["final"]["ES"], "3000")
        self.assertEqual(result["qualification"].startswith("host-only bounded entry trace"), True)

    def test_entry_probe_accepts_both_or_ax_ax_opcode_directions(self):
        for encoding in (bytes.fromhex("09 C0"), bytes.fromhex("0B C0")):
            with self.subTest(encoding=encoding.hex()):
                memory = bytearray(1 << 20)
                selector, ss = 0x1000, 0x2000
                start = (selector << 4) + 0x0100
                memory[start:start + 12] = (
                    bytes.fromhex("31 ED 55 9A 01 00 01 F0") + encoding + b"\x74\x00"
                )
                image = LoadedNE(
                    memory=memory,
                    image=object(),
                    segment_selectors={1: selector, 2: ss},
                    import_targets={(0xF001, 1): ImportTarget("KERNEL", "ordinal", None, 91)},
                    initial_cs=selector,
                    initial_ip=0x0100,
                    initial_ss=ss,
                    initial_sp=0,
                    loaded_bytes=12,
                )
                original = b"public synthetic test image"
                loader = NELoader(object())
                with patch.object(NELoader, "from_bytes", return_value=loader):
                    with patch.object(loader, "load", return_value=image):
                        result = run_probe(original, hashlib.sha256(original).hexdigest())
                self.assertTrue(result["reference_match"])
                self.assertTrue(result["input_bytes_unchanged"])

    def test_post_entry_trace_stores_synthetic_es_then_stops_at_next_import(self):
        memory = bytearray(1 << 20)
        selector, ss = 0x1000, 0x2000
        start = (selector << 4) + 0x0100
        code = bytes.fromhex(
            "31 ED 55 9A 01 00 01 F0 09 C0 74 00 "
            "8C 06 22 01 9A 01 00 01 F0"
        )
        memory[start:start + len(code)] = code
        image = LoadedNE(
            memory=memory,
            image=object(),
            segment_selectors={1: selector, 2: ss},
            import_targets={(0xF001, 1): ImportTarget("KERNEL", "ordinal", None, 91)},
            initial_cs=selector,
            initial_ip=0x0100,
            initial_ss=ss,
            initial_sp=0,
            loaded_bytes=len(code),
        )
        original = b"public synthetic test image with post-entry trace"
        loader = NELoader(object())
        with patch.object(NELoader, "from_bytes", return_value=loader):
            with patch.object(loader, "load", return_value=image):
                result = run_probe(original, hashlib.sha256(original).hexdigest())

        trace = result["post_entry_trace"]
        self.assertEqual(trace["status"], "next_import")
        self.assertEqual(trace["instructions_executed"], 2)
        self.assertEqual(trace["call_site"], "1000:0110")
        self.assertEqual(trace["target_location"], "F001:0001")
        self.assertEqual(trace["import"], {
            "module": "KERNEL", "kind": "ordinal", "ordinal": 91, "name": None,
        })
        self.assertEqual(bytes(memory[0x0122:0x0124]), bytes.fromhex("00 30"))
        self.assertEqual(result["task_stack_sentinel"], {
            "SS": "2000", "SP": "FFFC", "word": "0000",
        })
        self.assertEqual(result["guest_return"], {
            "CS": "1000", "IP": "010C", "post_import_instructions": 2,
            "success_branch_taken": False,
        })


if __name__ == "__main__":
    unittest.main()

