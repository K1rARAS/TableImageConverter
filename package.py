import paddlex
import importlib.metadata
import argparse
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--file', required=True, help='Your file name, e.g. main.py.')
args = parser.parse_args()

main_file = args.file
user_deps = [dist.metadata["Name"] for dist in importlib.metadata.distributions()]
deps_all = list(paddlex.utils.deps.BASE_DEP_SPECS.keys())
deps_need = [dep for dep in user_deps if dep in deps_all]

cmd = [
    "pyinstaller", main_file,
    "--collect-data", "paddlex",
    "--collect-binaries", "paddle"
]

for dep in deps_need:
    cmd += ["--copy-metadata", dep]

print("PyInstaller command:", " ".join(cmd))
subprocess.run(cmd, check=True)