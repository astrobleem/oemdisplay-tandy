"""Developer-only Open Watcom 16-bit DOS build; consumers use the shipped EXE."""
import argparse
import importlib.machinery
import os
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent

def build(home, output, target):
    home = home.resolve(strict=True)
    driver = home / "binnt/wcl.exe"
    if not driver.is_file() or not (home / "h/dos.h").is_file():
        raise ValueError("Complete Open Watcom DOS toolchain required")
    if target == "setup":
        aliases = importlib.machinery.SourceFileLoader("setup_alias_builder", str(HERE / "MAKESET.PY")).load_module()
        for name, data in aliases.generate().items():
            if (HERE / name).read_bytes() != data:
                raise ValueError("Regenerate expanded Setup input aliases first: " + name)
    output.mkdir(parents=True, exist_ok=False)
    for source in HERE.iterdir():
        if source.suffix in (".C", ".H", ".ASM"):
            shutil.copyfile(source, output / source.name)
    env = os.environ.copy()
    env.update(WATCOM=str(home), INCLUDE=str(home / "h"))
    env["PATH"] = str(home / "binnt") + os.pathsep + env.get("PATH", "")
    if target == "wrapper":
        commands = [
            [str(home / "binnt/wasm.exe"), "-zq", "-0", "-fo=XTCLEAN.OBJ", "XTCLEAN.ASM"],
            [str(home / "binnt/wlink.exe"), "system", "dos", "com", "option", "quiet", "name", "XTCLEAN.COM", "file", "XTCLEAN.OBJ"],
        ]
        logs = []
        for command in commands:
            result = subprocess.run(command, cwd=output, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            logs.append(result.stdout)
            (output / "BUILD.LOG").write_bytes(b"".join(logs))
            if result.returncode:
                raise ValueError("DOS wrapper build failed: " + str(result.returncode))
        return
    name = "FIXXT" if target == "finisher" else "XSETUP" if target == "xrsync" else "SETUP" if target == "setup" else "XRPREP"
    binary = "FIXXT" if target == "finisher" else "XSETUP" if target == "xrsync" else "SETUP" if target == "setup" else "PREPXR"
    flags = ["-zq", "-bt=dos", "-0", "-ms", "-s", "-k8192"] if target == "finisher" else ["-zq", "-bt=dos", "-0", "-ml", "-os"]
    result = subprocess.run([str(driver)] + flags + [
                             "-fe=" + binary + ".EXE", name + ".C"],
                            cwd=output, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    (output / "BUILD.LOG").write_bytes(result.stdout)
    print(result.stdout.decode("ascii", errors="replace"))
    if result.returncode:
        raise ValueError("DOS build failed: " + str(result.returncode))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--watcom", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--target", choices=("xrsync", "rc8", "setup", "finisher", "wrapper"), default="xrsync")
    args = parser.parse_args()
    build(args.watcom, args.out, args.target)
