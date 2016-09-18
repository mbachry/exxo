import mmap
import io
import struct
from collections import defaultdict
from pprint import pprint


# based on: https://github.com/maliubiao/python_elfutils (MIT licensed)


ELF_HEADER = 1 << 2
ELF_DYNAMIC = 1 << 4


ELF64 = 8
ELF32 = 4
ELF8 = 1


def load_struct(buffer, d, fmt):
    fmt_str = ''.join([x[1] for x in fmt])
    size = struct.calcsize(fmt_str)
    raw = buffer.read(size)
    if len(raw) != size:
        raise Exception('Truncated Stream')
    unpacked_raw = struct.unpack(fmt_str, raw)
    for i, m in enumerate(fmt):
        d[m[0]] = unpacked_raw[i]


elf32_hdr_format = (
        ('e_type', 'H'),
        ('e_machine', 'H'),
        ('e_version', 'I'),
        ('e_entry', 'I'),
        ('e_phoff', 'I'),
        ('e_shoff', 'I'),
        ('e_flags', 'I'),
        ('e_ehsize', 'H'),
        ('e_phentsize', 'H'),
        ('e_phnum', 'H'),
        ('e_shentsize', 'H'),
        ('e_shnum', 'H'),
        ('e_shstrndx', 'H')
)

elf64_hdr_format = (
        ('e_type', 'H'),
        ('e_machine', 'H'),
        ('e_version', 'I'),
        ('e_entry', 'Q'),
        ('e_phoff', 'Q'),
        ('e_shoff', 'Q'),
        ('e_flags', 'I'),
        ('e_ehsize', 'H'),
        ('e_phentsize', 'H'),
        ('e_phnum', 'H'),
        ('e_shentsize', 'H'),
        ('e_shnum', 'H'),
        ('e_shstrndx', 'H')
)

elf32_shdr_format = (
        ('sh_name', 'I'),
        ('sh_type', 'I'),
        ('sh_flags', 'I'),
        ('sh_addr', 'I'),
        ('sh_offset', 'I'),
        ('sh_size', 'I'),
        ('sh_link', 'I'),
        ('sh_info', 'I'),
        ('sh_addralign', 'I'),
        ('sh_entsize', 'I')
)

elf64_shdr_format = (
        ('sh_name', 'I'),
        ('sh_type', 'I'),
        ('sh_flags', 'Q'),
        ('sh_addr', 'Q'),
        ('sh_offset', 'Q'),
        ('sh_size', 'Q'),
        ('sh_link', 'I'),
        ('sh_info', 'I'),
        ('sh_addralign', 'Q'),
        ('sh_entsize', 'Q')
)


ELFSIG = b'\x7fELF'

ELFCLASS32 = 1
ELFCLASS64 = 2

SHT_STRTAB = 3
SHT_DYNAMIC = 6

DT_NEEDED = 1
DT_SONAME = 14
DT_RPATH = 15


def read_header(elf, buffer):
    buffer.seek(0)
    elf_header = elf['elf_header']
    elf_header['file_ident'] = buffer.read(ELF32)
    if elf_header['file_ident'] != ELFSIG:
        raise ValueError('This is not a ELF object')
    file_class = ord(buffer.read(ELF8))
    if file_class == ELFCLASS32:
        hdr_format = elf32_hdr_format
    elif file_class == ELFCLASS64:
        hdr_format = elf64_hdr_format
    else:
        raise ValueError('Unknown ELFCLASS: %d', file_class)
    elf_header['file_class'] = file_class
    elf_header['file_encoding'] = ord(buffer.read(ELF8))
    elf_header['file_version'] = ord(buffer.read(ELF8))
    # ignore 9 bytes
    buffer.seek(9, io.SEEK_CUR)
    load_struct(buffer, elf_header, hdr_format)


def read_section_header(elf, buffer):
    elf_header = elf['elf_header']
    sections = elf['sections']
    e_shoff = elf_header['e_shoff']
    buffer.seek(e_shoff)
    e_shnum = elf_header['e_shnum']
    if elf_header['file_class'] == ELFCLASS32:
        shdr_format = elf32_shdr_format
    elif elf_header['file_class'] == ELFCLASS64:
        shdr_format = elf64_shdr_format
    else:
        raise ValueError('Unknown ELFCLASS: %d' % elf_header['file_class'])
    for _ in range(e_shnum):
        section = {}
        load_struct(buffer, section, shdr_format)
        sections.append(section)


def build_strtab(buffer, section):
    buffer.seek(section['sh_offset'])
    size = section['sh_size']
    raw = buffer.read(size)
    strtab = {}
    strend = b'\x00'
    i = 0
    while i < size:
        if raw[i:i + 1] != strend:
            i += 1
            continue
        j = i + 1
        end = raw.find(strend, j)
        if end == -1:
            break
        name = raw[j:end]
        more = name.find(b'.', 1)
        if more > 0:
            strtab[j + more] = name[more:]
        strtab[j] = name
        i = end
    return strtab


def read_strtab(elf, buffer):
    sections = elf['sections']
    strtab_sections = []
    for section in sections:
        if section['sh_type'] == SHT_STRTAB:
            strtab_sections.append(section)
    for section in strtab_sections:
        buffer.seek(section['sh_offset'])
        if b'.text' in buffer.read(section['sh_size']):
            shstrtab_section = section
            break
    else:
        raise RuntimeError('shstrtab section missing')

    shstrtab = build_strtab(buffer, shstrtab_section)
    for section in sections[1:]:
        section['sh_name'] = shstrtab[section['sh_name']]
    for section in strtab_sections:
        name = section['sh_name'].decode()
        strtab = build_strtab(buffer, section)
        elf['strtabs'][name] = strtab


# def read_dynamic(elf, buffer):
#     sections = elf['sections']
#     dynamic = None
#     for section in sections:
#         if section['sh_type'] == SHT_DYNAMIC:
#             dynamic = section
#             break
#     dynamic_list = elf['dynamic']
#     buffer.seek(dynamic['sh_offset'])
#     total = dynamic['sh_size'] / dynamic['sh_entsize']
#     if elf['elf_header']['file_class'] == ELFCLASS32:
#         for entry in range(int(total)):
#             dtag, value = struct.unpack('II', buffer.read(ELF64))
#             dynamic_list.append({dtag: value})
#             if not dtag:
#                 break
#     else:
#         for entry in range(int(total)):
#             dtag, value = struct.unpack('QQ', buffer.read(2 * ELF64))
#             dynamic_list.append({dtag: value})
#             if not dtag:
#                 break
#     in_symtab = [DT_NEEDED, DT_SONAME, DT_RPATH]
#     strtabs = elf['strtabs']
#     strtab = {}
#     dyntab = {}
#     if '.strtab' in strtabs:
#         strtab = strtabs['.strtab']
#     if '.dynstr' in strtabs:
#         dyntab = strtabs['.dynstr']
#     final = defaultdict(list)
#     for entry in dynamic_list:
#         d_tag = list(entry.keys())[0]
#         if d_tag in in_symtab:
#             if not d_tag:
#                 continue

def read_dynamic(elf, buffer):
    sections = elf['sections']
    dynamic = None
    for section in sections:
        if section['sh_type'] == SHT_DYNAMIC:
            dynamic = section
            break
    dynamic_list = elf['dynamic']
    buffer.seek(dynamic['sh_offset'])
    total = dynamic['sh_size'] / dynamic['sh_entsize']
    if elf['elf_header']['file_class'] == ELFCLASS32:
        for entry in range(int(total)):
            dtag, value = struct.unpack('II', buffer.read(ELF64))
            dynamic_list.append({dtag: value})
            if not dtag:
                break
    else:
        for entry in range(int(total)):
            dtag, value = struct.unpack('QQ', buffer.read(2 * ELF64))
            dynamic_list.append({dtag: value})
            if not dtag:
                break
    in_symtab = [DT_NEEDED, DT_SONAME, DT_RPATH]
    strtabs = elf['strtabs']
    strtab = {}
    dyntab = {}
    if '.strtab' in strtabs:
        strtab = strtabs['.strtab']
        strtab_section = [s for s in sections if s['sh_name'] == b'.strtab'][0]
    if '.dynstr' in strtabs:
        dyntab = strtabs['.dynstr']
        dyntab_section = [s for s in sections if s['sh_name'] == b'.dynstr'][0]
    final = defaultdict(list)
    for entry in dynamic_list:
        d_tag = list(entry.keys())[0]
        if d_tag in in_symtab:
            if not d_tag:
                continue
            value = entry[d_tag]
            if not value:
                continue
            if value in strtab:
                name = strtab[value]
                if d_tag == DT_RPATH:
                    off = strtab_section['sh_offset'] + value
                    elf['rpath_offset'] = off
            elif value in dyntab:
                name = dyntab[value]
                if d_tag == DT_RPATH:
                    off = dyntab_section['sh_offset'] + value
                    elf['rpath_offset'] = off
            entry[d_tag] = name
            final[d_tag].append(name)
    elf['dynamic'] = dict(final)


def readelf(path):
    elf = {
        'elf_header': {},
        'sections': [],
        'strtabs': {},
        'dynamic': [],
    }
    f = open(path, 'rb')
    buffer = mmap.mmap(f.fileno(), 0, mmap.MAP_PRIVATE, mmap.PROT_READ)
    read_header(elf, buffer)
    read_section_header(elf, buffer)
    read_strtab(elf, buffer)
    read_dynamic(elf, buffer)
    buffer.close()
    f.close()
    return elf
