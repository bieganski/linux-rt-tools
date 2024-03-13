#!/usr/bin/env python3

from pathlib import Path
from elftools.elf.elffile import ELFFile
from typing import Generator
import logging

logging.basicConfig(level=logging.INFO)

def dynamic_symbols(path: Path) -> Generator[str, None, None]:
    elf_file = ELFFile(path.open("rb"))
    dynamic_symbols = elf_file.get_section_by_name('.dynsym')
    
    if dynamic_symbols is None:
        logging.error(f"{path} does not have a dynamic symbol section.")
        return

    for symbol in dynamic_symbols.iter_symbols():
        if symbol["st_size"] > 0:
            yield symbol.name

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Print to stdout dynamic (defined) symbols of a shared library.')
    parser.add_argument('shared_libs', nargs="+", type=Path, help='Path to the shared library (ELF file)')

    args = parser.parse_args()
    
    allsyms = set()
    for so in args.shared_libs:
        for sym in dynamic_symbols(path=so):
            allsyms.add((sym, so))
    for sym, so in allsyms:
        print(f"{sym} {so}")

