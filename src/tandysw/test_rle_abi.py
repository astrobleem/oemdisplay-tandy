#!/usr/bin/env python3
"""Focused regressions for the RLE helper's emitted near-call ABI."""
import unittest
from importlib.machinery import SourceFileLoader
from pathlib import Path

RLEABITEST = SourceFileLoader(
    "rleabittest_under_test", str(Path(__file__).with_name("RLEABITEST.PY"))
).load_module()


GOOD_LISTING = """\
 0361  E8 0609 R            call rle_store_pixel
 0439  E8 0609 R            call rle_store_pixel
 0461  E8 0609 R            call rle_store_pixel
 049B  E8 0609 R            call rle_store_pixel
 0635                        rlesp_ok:
 0635  F8                    clc
 0636  C3                    retn
 0637                        rlesp_bad:
 0637  F9                    stc
 0638  C3                    retn
 0146  CA 0018               ret 24
 0642  CA 0008               ret 8
 023A  26: 80 7D 1B 00        cmp byte ptr es:[di+rsSkip],0
"""

GOOD_SOURCE = """\
rsSkip      equ 27
rsDeltaX    equ 28
rlen_pending:
    cmp byte ptr es:[di+rsSkip],0
rlen_apply_delta_x:
rlesp_ok:
    clc
    retn
rlesp_bad:
    stc
    retn
"""


class RleAbiAuditTests(unittest.TestCase):
    def test_both_near_helper_outcomes_balance_call_stack(self):
        result = RLEABITEST.audit_listing(GOOD_LISTING)
        self.assertEqual(result["near_call_sites"], ["0361", "0439", "0461", "049B"])
        self.assertEqual(result["helper_stack_delta_bytes"], {"success": 0, "failure": 0})
        self.assertEqual(result["far_cleanup"], {"RLEInit": 24, "RLENextRow": 8})

    def test_far_retf_is_rejected_for_each_helper_outcome(self):
        bad = GOOD_LISTING.replace("0636  C3", "0636  CB").replace("0638  C3", "0638  CB")
        with self.assertRaisesRegex(AssertionError, "success helper path"):
            RLEABITEST.audit_listing(bad)
        bad = GOOD_LISTING.replace("0636  C3", "0636  CB")
        with self.assertRaisesRegex(AssertionError, "success helper path"):
            RLEABITEST.audit_listing(bad)
        bad = GOOD_LISTING.replace("0638  C3", "0638  CB")
        with self.assertRaisesRegex(AssertionError, "failure helper path"):
            RLEABITEST.audit_listing(bad)

    def test_near_call_and_both_callee_far_cleanups_are_required(self):
        with self.assertRaisesRegex(AssertionError, "four emitted near CALL"):
            RLEABITEST.audit_listing(GOOD_LISTING.replace("E8 0609", "9A 0609", 1))
        with self.assertRaisesRegex(AssertionError, "RLEInit"):
            RLEABITEST.audit_listing(GOOD_LISTING.replace("CA 0018", "C3", 1))
        with self.assertRaisesRegex(AssertionError, "RLENextRow"):
            RLEABITEST.audit_listing(GOOD_LISTING.replace("CA 0008", "C3", 1))

    def test_byte_sized_delta_skip_is_emitted_at_state_offset_27(self):
        result = RLEABITEST.audit_listing(GOOD_LISTING)
        self.assertEqual(result["delta_skip_compare"], "byte [ES:DI+27]")
        self.assertEqual(RLEABITEST.audit_source(GOOD_SOURCE)["delta_skip_width"], 1)

    def test_overlapping_word_read_is_rejected(self):
        bad_listing = GOOD_LISTING.replace(
            "26: 80 7D 1B 00        cmp byte ptr es:[di+rsSkip],0",
            "26: 8B 45 1B            mov ax,es:[di+rsSkip]")
        with self.assertRaisesRegex(AssertionError, "byte compare"):
            RLEABITEST.audit_listing(bad_listing)
        bad_source = GOOD_SOURCE.replace(
            "cmp byte ptr es:[di+rsSkip],0", "mov ax,es:[di+rsSkip]")
        with self.assertRaisesRegex(AssertionError, "test only the byte"):
            RLEABITEST.audit_source(bad_source)

    def test_source_requires_explicit_near_returns_on_both_paths(self):
        self.assertEqual(RLEABITEST.audit_source(GOOD_SOURCE)["near_helper_returns"], 2)
        bad_source = GOOD_SOURCE.replace("retn", "ret")
        with self.assertRaisesRegex(AssertionError, "explicitly use RETN"):
            RLEABITEST.audit_source(bad_source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
