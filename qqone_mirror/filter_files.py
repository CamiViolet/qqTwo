#!/usr/bin/env python3
"""
Delete files that do not match any of the required regexes.

Usage:
    python filter_files.py --path <path> --patterns <regex1,regex2,...>
                           [--keep-extensions <ext1,ext2,...>]
                           [--keep-names <name1,name2,...>]

Example:
    python filter_files.py --path ./sources --patterns dds_stream_write,dds_stream_read
    python filter_files.py --path ./sources --patterns dds.?stream_write --keep-extensions .h,.hpp --keep-names cmakelists.txt
"""

import argparse
import os
import re
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description="Delete files that do not match any of the given regex-patterns."
    )
    parser.add_argument("--path", required=True, help="Root directory to traverse.")
    parser.add_argument("--patterns", required=True, help="Comma-separated list of regexes to search for in each file.")
    parser.add_argument("--keep-extensions", default="",
                        help="Comma-separated list of file extensions to always keep.")
    parser.add_argument("--keep-names", default="",
                        help="Comma-separated list of exact filenames (case-insensitive) to always keep.")
    return parser.parse_args()


def is_always_kept(filepath, keep_extensions, keep_names):
    name = os.path.basename(filepath).lower()
    ext = os.path.splitext(name)[1].lower()
    return ext in keep_extensions or name in keep_names


def file_contains_any(filepath, patterns):
    if any(p.search(filepath) for p in patterns):
        return True
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return any(p.search(content) for p in patterns)
    except OSError as e:
        print(f"WARNING: Cannot read '{filepath}': {e}", file=sys.stderr)
        return True  # keep files we cannot read


def main():
    args = parse_args()

    raw_patterns = [s for s in args.patterns.split(",") if s]
    if not raw_patterns:
        print("ERROR: no patterns provided.", file=sys.stderr)
        sys.exit(1)
    try:
        patterns = [re.compile(s, re.IGNORECASE) for s in raw_patterns]
    except re.error as e:
        print(f"ERROR: invalid regex: {e}", file=sys.stderr)
        sys.exit(1)

    keep_extensions = {e.strip().lower() for e in args.keep_extensions.split(",") if e.strip()}
    keep_names = {n.strip().lower() for n in args.keep_names.split(",") if n.strip()}

    root = os.path.abspath(args.path)
    if not os.path.isdir(root):
        print(f"ERROR: '{root}' is not a directory.", file=sys.stderr)
        sys.exit(1)

    deleted = 0
    kept = 0

    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if is_always_kept(filepath, keep_extensions, keep_names) or file_contains_any(filepath, patterns):
                kept += 1
            else:
                try:
                    os.remove(filepath)
                    print(f"deleted: {filepath}")
                except OSError as e:
                    print(f"WARNING: Cannot delete '{filepath}': {e}", file=sys.stderr)
                    kept += 1
                    continue
                deleted += 1

    print(f"\nDone. Deleted: {deleted}  |  Kept: {kept}")


if __name__ == "__main__":
    main()
