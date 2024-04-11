#!/usr/bin/env python3
import argparse
from elftools.elf.elffile import ELFFile
from pathlib import Path

def get_section_offset_and_size(path: Path, section_name) -> tuple[int, int]:
    elf_file = ELFFile(path.open("rb"))
    for section in elf_file.iter_sections():
        if section.name == section_name:
            return (section['sh_offset'], section['sh_size'])
    raise ValueError(f"No section '{section_name}' in file {path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract file offset of a section from an ELF file.')
    parser.add_argument('-e', '--elf', required=True, type=Path, help='Path to the ELF file')
    parser.add_argument('-s', '--section', required=True, type=str, help='Name of the section to extract the offset for')
    parser.add_argument('-b', '--bytes', required=True, type=Path, help='Path to bytes to overwrite section with. Can not be longer than section size.')
    parser.add_argument('-o', '--output', required=True, type=Path, help='New ELF path.')

    args = parser.parse_args()

    old_elf : Path = args.elf
    new_elf : Path = args.output
    patch: bytes = args.bytes.read_bytes()

    offset, size = get_section_offset_and_size(path=args.elf, section_name=args.section)

    print(f"patch size={len(patch)}, section size={size}")
    if size < len(patch):
        raise ValueError("Too small section to be patched.")

    with new_elf.open("wb") as f:
        f.write(old_elf.read_bytes())
        f.seek(offset)
        f.write(patch)

    print(f"ELF patched at offset {hex(offset)} written to {new_elf}")
