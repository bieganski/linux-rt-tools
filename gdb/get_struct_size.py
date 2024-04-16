#!/usr/bin/env python3

from typing import Generator
from collections import namedtuple

from elftools.elf.elffile import ELFFile
from elftools.dwarf.die import DIE
from elftools.dwarf.compileunit import CompileUnit


# { field_xpath , ( offset, field_len ) }
# entries might overlap (because of unions).
StructLayoutType = dict[str, tuple[int, int]]

def get_struct_layout(elf_file, type_name) -> StructLayoutType:
    with open(elf_file, 'rb') as f:
        elf = ELFFile(f)

        if (di := elf.get_dwarf_info()) is None:
            print("No DWARF information found.")
            return
        
        def die_iterator_factory() -> Generator[tuple[CompileUnit, DIE], None, None]:
            for cu in di.iter_CUs():
                for die in cu.iter_DIEs():
                    yield cu, die
        
        def find_die_by_offset(offset: int) -> DIE:
            for _, die in die_iterator_factory():
                if die.offset == offset:
                    return die
            raise ValueError(f"Could not find DIE at offset {hex(offset)}")
    
        def die_normalize(die: DIE) -> DIE:
            """
            Strip "DW_TAG_typedef" and "DW_TAG_volatile_type" tags.
            """
            while True:
                if die.tag not in ["DW_TAG_typedef", "DW_TAG_volatile_type"]:
                    return die
                AT_type_offset = die.attributes["DW_AT_type"].value
                die = find_die_by_offset(AT_type_offset)
    
        # Find top-level struct DIE.
        for _, die in die_iterator_factory():
            die = die_normalize(die)
            if die.tag in ["DW_TAG_structure_type", "DW_TAG_union_type", "DW_TAG_base_type"]:
                if "DW_AT_name" in die.attributes and die.attributes["DW_AT_name"].value.decode('utf-8') == type_name:
                    top_level_die : DIE = die; del die
                    break
        else:
            raise ValueError(f"Could not find struct '{type_name}' definition in '{elf_file}'s DWARF.")
        
        # TODO 1: .decode(utf-8)
        # TODO 2: enums for DW_AT

        mock_zero_value = namedtuple("_", ["value"])(value=0)
        mock_nullstr_value = namedtuple("_", ["value"])(value=b"")

        def _recursion(top_level_die: DIE, write_only_res: StructLayoutType, cur_xpath: str, cur_offset: int, first_iter: bool):
            
            if first_iter:
                top_level_size = top_level_die.attributes["DW_AT_byte_size"].value
                write_only_res["/"] = (cur_offset, top_level_size)
            
            if top_level_die.tag == "DW_TAG_base_type":
                return
            
            assert top_level_die.tag in ["DW_TAG_union_type", "DW_TAG_structure_type"]
            
            # Find all member children.
            for die in top_level_die.iter_children():
                die = die_normalize(die)
                AT_type_die = find_die_by_offset(die.attributes["DW_AT_type"].value)
                AT_type_die = die_normalize(AT_type_die)

                maybe_member_name = die.attributes.get("DW_AT_name", mock_nullstr_value).value.decode("utf-8")
                member_size = AT_type_die.attributes["DW_AT_byte_size"].value
                
                member_offset = die.attributes.get("DW_AT_data_member_location", mock_zero_value).value
                
                if maybe_member_name is None:
                    assert AT_type_die.has_children
                    assert AT_type_die.tag == "DW_TAG_union_type"
                else:
                    # AT_type_die can be either base,struct or union.
                    write_only_res[f"{cur_xpath}/{maybe_member_name}"] = (cur_offset + member_offset, member_size)
                
                if AT_type_die.tag in ["DW_TAG_union_type", "DW_TAG_structure_type"]:
                    _recursion(
                        top_level_die=AT_type_die,
                        write_only_res=res,
                        cur_xpath=(cur_xpath if not maybe_member_name else f"{cur_xpath}/{maybe_member_name}"),
                        cur_offset=cur_offset + member_offset,
                        first_iter=False,
                    )
        
        def recursion(top_level_die: DIE, res: StructLayoutType):
            _recursion(
                top_level_die=top_level_die,
                write_only_res=res,
                cur_xpath="",
                cur_offset=0,
                first_iter=True,
            )

        res : StructLayoutType = {}
        recursion(top_level_die=top_level_die, res=res)
        return res

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Parse ELF DWARF and get DW_AT_byte_size field of DW_AT_name <struct name>.')
    parser.add_argument('-e', "--elf", required=True, help='Path to the ELF file')
    parser.add_argument('-n', "--struct-name", required=True, help='Name of the struct')

    args = parser.parse_args()

    layout = get_struct_layout(args.elf, args.struct_name)

    from pprint import pprint
    pprint(layout)
