import unittest

from api_fixture import INSTANCE_SELECTOR, LPARAM, WINDOWS, run_api_callback_fixture


class Win16APIFixtureTests(unittest.TestCase):
    def test_getversion_returns_to_8086_guest_and_enumwindows_calls_guest(self):
        result = run_api_callback_fixture()

        self.assertEqual(result.version_word, 0x0003)
        self.assertEqual(
            [(target.module, target.name) for target in result.api_calls],
            [
                ("KERNEL", "GetVersion"),
                ("KERNEL", "MakeProcInstance"),
                ("USER", "EnumWindows"),
            ],
        )
        self.assertEqual(result.proc_instance, (0xE000, 1))
        self.assertEqual(result.enum_result, 1)
        self.assertEqual(
            [invocation.window for invocation in result.callback_invocations],
            list(WINDOWS),
        )
        self.assertTrue(all(invocation.returned_nonzero for invocation in result.callback_invocations))
        self.assertTrue(all(invocation.lparam == LPARAM for invocation in result.callback_invocations))
        self.assertTrue(all(invocation.instance_selector == INSTANCE_SELECTOR
                            for invocation in result.callback_invocations))
        self.assertEqual(result.last_callback_window, WINDOWS[-1])
        self.assertEqual(result.callback_lparam, LPARAM)
        self.assertTrue(result.caller_ds_restored)
        self.assertEqual(result.final_stack_pointer, 0x0100)
        self.assertLessEqual(result.instructions, 128)

    def test_zero_guest_callback_return_stops_enumwindows(self):
        result = run_api_callback_fixture(callback_returns_nonzero=False)

        self.assertEqual(result.enum_result, 0)
        self.assertEqual(
            [invocation.window for invocation in result.callback_invocations],
            [WINDOWS[0]],
        )
        self.assertFalse(result.callback_invocations[0].returned_nonzero)
        self.assertEqual(result.final_stack_pointer, 0x0100)
        self.assertTrue(result.caller_ds_restored)


if __name__ == "__main__":
    unittest.main()
