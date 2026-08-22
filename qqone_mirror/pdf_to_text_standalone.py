# Script: pdf_to_text_standalone.py
# Description: Convert PDF files to text/markdown. No external config or library dependencies.
# Usage:
#   python pdf_to_text_standalone.py --dir <directory>
#   python pdf_to_text_standalone.py --pdf_file <path_to_pdf>
# Examples:
#   python pdf_to_text_standalone.py --dir "C:\docs\pdfs" --force
#   python pdf_to_text_standalone.py --pdf_file "C:\docs\spec.pdf" --type omg --split_chapters

from collections import defaultdict
import re
import fitz  # pip install PyMuPDF
import os
import argparse
import sys
import traceback
import pdb


def excepthook(type, value, tb):
    traceback.print_exception(type, value, tb)
    pdb.pm()


def normalize_to_C_symbol(word):
    """Replace any character that is not alphanumeric or underscore with underscore."""
    norm = re.sub(r'[^a-zA-Z0-9_]', '_', word)
    while '__' in norm:
        norm = norm.replace('__', '_')
    return norm


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Convert PDF files to text/markdown. Pass all paths via command line."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--dir",
        help="Directory to scan recursively for PDF files to convert."
    )
    group.add_argument(
        "--pdf_file",
        help="Path to a single PDF file to convert."
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Force overwrite of existing output files."
    )
    parser.add_argument(
        "--type", choices=["none", "omg"], default="none",
        help="Conversion style: 'none' for plain text, 'omg' for OMG formatting (default: none)."
    )
    parser.add_argument(
        "--split_chapters", action="store_true",
        help="Split output by chapters detected by heading level 1."
    )
    parser.add_argument(
        "-v", action="store_true",
        help="Verbose console output."
    )
    return parser.parse_args()


def pdf_to_text(pdf_path, md_path, args):
    """Convert a PDF file to a markdown file."""
    pdf_document = fitz.open(pdf_path)

    full_text = []
    chapters = defaultdict(list)
    chapter_idx = 0
    chapter_title = {chapter_idx: ""}

    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        page_text = page.get_text()

        for line in page_text.splitlines():
            line = line.strip()
            if not line or line == '.':
                continue

            # Detect numbered headings, e.g. "1.2 Overview of this Specification"
            match = re.match(r'^(\d+(\.\d+)*)\s+([A-Z].*)$', line)
            if match:
                numbers = match.group(1)
                title = match.group(3)
                level = 1 + numbers.count('.')
                if level == 1:
                    chapter_idx = int(numbers)
                    chapter_title[chapter_idx] = title
                line = f"\n{'#' * level} {line}\n"

            # Replace bullet point (•) with Markdown asterisk
            if line.startswith('•'):
                line = '\n' + line.replace('•', '*', 1)

            full_text.append(line)
            chapters[chapter_idx].append(line)

        full_text.append("")
        chapters[chapter_idx].append("")

    if args.split_chapters:
        for idx, lines in chapters.items():
            title_norm = normalize_to_C_symbol(chapter_title[idx]).lower()
            chapter_path = f"{pdf_path}.chapter_{idx}_{title_norm}.md"
            with open(chapter_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
            print(f"PDF exported to: {chapter_path}")

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(full_text))
    print(f"PDF exported to: {md_path}")


def process_directory(directory, args):
    if not os.path.isdir(directory):
        print(f"ERROR: Directory not found: {directory}")
        sys.exit(1)

    print(f"Processing directory: {directory}")
    for root, _dirs, files in os.walk(directory):
        for file_name in files:
            if file_name.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file_name)
                md_path = f"{pdf_path}.md"
                if not args.force and os.path.exists(md_path):
                    if args.v:
                        print(f"Skipping {md_path} (already exists). Use --force to overwrite.")
                    continue
                pdf_to_text(pdf_path, md_path, args)


def process_single_file(pdf_path, args):
    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}")
        sys.exit(1)
    md_path = f"{pdf_path}.md"
    if not args.force and os.path.exists(md_path):
        print(f"Skipping {md_path} (already exists). Use --force to overwrite.")
        return
    pdf_to_text(pdf_path, md_path, args)


if __name__ == "__main__":
    sys.excepthook = excepthook

    args = parse_arguments()

    if args.dir:
        process_directory(args.dir, args)
    else:
        process_single_file(args.pdf_file, args)
