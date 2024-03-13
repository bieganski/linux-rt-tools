#!/usr/bin/env python3

import subprocess
from pathlib import Path
import logging
from typing import Generator

logging.basicConfig(level=logging.INFO)

def run_shell(cmd: str) -> tuple[str, str]:
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
    stdout, stderr = process.communicate()
    if (ecode := process.returncode):
        raise ValueError(f"Command <{cmd}> exited with {ecode}")
    return stdout, stderr

def shared_libs_in_dir(dir: Path) -> Generator[Path, None, None]:
    assert dir.is_dir()
    for p in dir.iterdir():
        if not p.is_file():
            continue
        if is_shared_lib(p):
            yield p

def is_shared_lib(path : Path) -> bool:
    with path.open("rb") as p:
        ET_DYN, min_size = 3, 16 + 1
        #define EI_NIDENT 16
        if len(header := p.read(min_size)) != min_size:
            return False
        # NOTE: PIE executable are considered shared libs as well.
        return (header[1:4] == "ELF".encode()) and (header[-1] == ET_DYN)

def shared_libs_of_process(pid: int, lenient: bool = True) -> Generator[Path, None, None]:
    mapfile = Path(f"/proc/{pid}/maps")
    try:
        lines = mapfile.read_text().splitlines()
    except Exception as e:
        if lenient:
            logging.warning(e); return
        else:
            raise ValueError(e)
    for l in lines:
        words = l.split()
        if len(words) == 6 and not words[-1].startswith("["):
            p = Path(words[-1])
            if p.is_file() and is_shared_lib(p):
                yield p

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser(usage="Print shared libraries to stdout, either in use (opened by PID process) or present in filesystem (by DIR).")
    subparsers = parser.add_subparsers(required=True)

    by_pid_parser    = subparsers.add_parser("pid")
    by_dir_parser    = subparsers.add_parser("dir")
    find_open_parser = subparsers.add_parser("find_open")

    by_pid_parser.add_argument("pids", nargs="+", type=int)
    by_dir_parser.add_argument("dirs", nargs="+", type=Path)
    find_open_parser.add_argument("path", type=Path)

    args = parser.parse_args()
    
    lst = []

    if "dirs" in args:
        for dir in args.dirs:
            lst.extend(shared_libs_in_dir(dir))
    elif "pids" in args:
        for pid in args.pids:
            lst.extend(shared_libs_of_process(pid))
    elif "path" in args:
        # find pids that have file <path> opened.
        path = Path(args.path).absolute()
        allpid = [int(x) for x in run_shell("ps --no-headers -eo pid")[0].split()]
        for pid in allpid:
            if path in shared_libs_of_process(pid):
                lst.append(pid)
    else:
        assert False

    for x in set(lst):
        print(str(x))