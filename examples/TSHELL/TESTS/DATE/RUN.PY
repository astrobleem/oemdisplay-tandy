"""Compile and run only DTCORE against fake setters; no real clock API."""
import os
import pathlib
import subprocess

here = pathlib.Path(__file__).resolve().parent
shell = here.parents[1]
binary = here / "DTTEST"
command = [
    "gcc", "-x", "c", "-std=c89", "-Wall", "-Wextra", "-Werror", "-pedantic",
    "-fsanitize=address,undefined", "-g", "-I", str(shell),
    str(shell / "DTCORE.C"), str(here / "DTTEST.C"), "-o", str(binary),
]
subprocess.run(command, check=True)
environment = os.environ.copy()
# LeakSanitizer cannot inspect processes under this workspace's tracing.
# AddressSanitizer and UndefinedBehaviorSanitizer remain enabled.
environment["ASAN_OPTIONS"] = "detect_leaks=0"
result = subprocess.run([str(binary)], env=environment, check=True,
                        text=True, capture_output=True)
(here / "TEST.LOG").write_text(result.stdout + result.stderr)
print(result.stdout, end="")
