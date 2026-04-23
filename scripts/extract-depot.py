#!/usr/bin/env python3
"""Extract files from Logitech Options+ .depot container format.

Format: 4-byte magic (0x20170110) | 4-byte JSON header length | JSON header | files...
Each file: 4-byte little-endian size | raw file data

Usage:
    python3 scripts/extract-depot.py <depot-file> [--output-dir <dir>]
    python3 scripts/extract-depot.py --all <depot-dir> [--output-dir <dir>]
"""

import argparse
import json
import struct
import sys
from pathlib import Path

SKIP_MAGIC = 0x20170110

def extract_depot(depot_path: Path, output_dir: Path) -> list[str]:
    """Extract all files from a .depot container."""
    with depot_path.open('rb') as input:
        magic = struct.unpack('<I', input.read(4))[0]
        if magic != SKIP_MAGIC:
            print(f"  Skip: not a depot file (magic 0x{magic:08x})", file=sys.stderr)
            return []

        json_len: int = struct.unpack('<I', input.read(4))[0]
        header: dict = json.loads(input.read(json_len))
        files: list[dict] = header.get('files', [])

        output_dir.mkdir(parents=True, exist_ok=True)
        extracted: list[str] = []

        for entry in files:
            name: str = entry['name']
            size: int = struct.unpack('<I', input.read(4))[0]
            data: bytes = input.read(size)

            out_path: Path = output_dir / name
            with out_path.open('wb') as out:
                out.write(data)
            extracted.append(name)

    return extracted

def is_image_file(filepath: Path | str) -> bool:
    return Path(filepath).suffix.lower() in ('.png', '.jpg', '.gif')

def main():
    parser = argparse.ArgumentParser(description='Extract Logitech Options+ .depot files')
    parser.add_argument('input', help='Single .depot file or directory (with --all)')
    parser.add_argument('--all', action='store_true', help='Extract all .depot files in directory')
    parser.add_argument('--output-dir', default='extracted', help='Output directory')
    parser.add_argument('--images-only', action='store_true', help='Only extract PNG/JPG/GIF files')
    parser.add_argument('--list', action='store_true', help='List contents without extracting')
    args = parser.parse_args()

    if args.all:
        depot_dir: Path = Path(args.input)
        depot_files = list(depot_dir.glob('*.depot'))
    else:
        depot_files = [Path(args.input)]

    total_files = 0
    total_images = 0

    for depot_path in sorted(depot_files):
        depot_name: str = depot_path.stem

        try:
            with depot_path.open('rb') as input:
                magic: int = struct.unpack('<I', input.read(4))[0]
                if magic != SKIP_MAGIC:
                    continue
                json_len: int = struct.unpack('<I', input.read(4))[0]
                header: dict = json.loads(input.read(json_len))
        except Exception:
            continue

        files: list[dict] = header.get('files', [])
        file_names: list[str] = [file['name'] for file in files]
        has_front: bool = 'front.png' in file_names
        has_metadata: bool = 'metadata.json' in file_names

        if args.list:
            if has_front or has_metadata:
                img_count: int = sum(1 for filename in file_names if is_image_file(filename))
                print(f"{depot_name}: {len(files)} files ({img_count} images)")
                if has_metadata:
                    print(f"  has metadata.json")
            continue

        if args.images_only and not has_front:
            continue

        out_dir = Path(args.output_dir) / depot_name
        extracted: list[str] = extract_depot(depot_path, out_dir)

        if args.images_only:
            for name in extracted:
                remove_path: Path = out_dir / name
                if not is_image_file(remove_path):
                    remove_path.unlink()

        img_count: int = sum(1 for filename in extracted if is_image_file(filename))
        total_files += len(extracted)
        total_images += img_count

        if extracted:
            print(f"  {depot_name}: {len(extracted)} files ({img_count} images)")

    print(f"\nTotal: {total_files} files, {total_images} images")

if __name__ == '__main__':
    main()
