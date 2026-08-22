# Script: qModel_2.py
# Description: Parse an AUTOSAR model
# Usage: python qModel_2.py <path_to_arxml_file>
# Example: 
#   python pdf_to_text.py --force --pdf_file "C:\Dev_Analisys\kb0\imports\pdf\DDS Security 1.2.pdf"

from collections import defaultdict
import re
import fitz  # pip install PyMuPDF
import json
import os
import argparse
import sys
from library import normalize_to_C_symbol, load_config, excepthook


def parse_arguments():
    parser = argparse.ArgumentParser(description="Convert PDF files to text.")
    parser.add_argument("-a", "--activity", default=None, help="Activity folder containing PDF files to convert. If omitted, all activities are processed.")
    parser.add_argument("--force", action="store_true", help="Force overwrite of existing text files.")
    parser.add_argument("--type", choices=["none", "omg", ], default="none",
                        help="Converion to Markdown: 'none' for plain text, 'omg' for OMG formatting (default: none).")
    parser.add_argument("--pdf_file", default=None,
                        help="Path to a single PDF file to convert. If provided, pdf_import_dir from config is ignored.")
    parser.add_argument("--split_chapters", action="store_true", help="Split output by chapters (detected by heading level 1).")
    parser.add_argument("-v", action="store_true", help="Verbose console output")

    return parser.parse_args()


def pdf_to_text(pdf_path, md_path, args):
    """
    Converts a PDF file to a markdown file.

    :param pdf_path: Path to the input PDF file.
    :param md_path: Path to the output markdown file.
    """
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)

    # Iterate through each page in the PDF
    full_text = []
    chapters = defaultdict(list)
    chapter_idx = 0
    chapter_title = {chapter_idx: ""}
    for page_num in range(len(pdf_document)):
        # Get the page
        page = pdf_document[page_num]

        # Extract text from the page
        page_text = page.get_text()

        lines = page_text.splitlines()
        for line in lines:
            line = line.strip()
            if line.strip() == "":
                continue
            if line.strip() == ".":
                continue

            # Check if the line is a heading e.g. it matches '1.2 Overview of this Specification'
            regex = r'^(\d+(\.\d+)*)\s+([A-Z].*)$'
            match = re.match(regex, line)
            if match:
                numbers = match.group(1)
                title = match.group(3)
                level = 1 + numbers.count('.')
                if level==1:
                    chapter_idx = int(numbers)
                    chapter_title[chapter_idx] = title
                line = f"\n{'#' * level} {line}\n"

            # Replace bullet point (•) followed by space with asterisk (*)
            if line.startswith('•'):
                line = '\n' + line.replace('•', '*', 1)

            full_text.append(line)
            chapters[chapter_idx].append(line)

        full_text.append("")  
        chapters[chapter_idx].append("")  

    # Create or overwrite the markdown file
    if args.split_chapters:
        for chapter_idx, lines in chapters.items():
            title_normalized = normalize_to_C_symbol(chapter_title[chapter_idx]).lower()
            chapter_md_path = f"{pdf_path}.chapter_{chapter_idx}_{title_normalized}.md"
            with open(chapter_md_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write("\n".join(lines))
            print(f"PDF exported to: {chapter_md_path}")

    with open(md_path, 'w', encoding='utf-8') as txt_file:

        # Write the text to the file
        txt_file.write("\n".join(full_text))

    print(f"PDF exported to: {md_path}")


if __name__ == "__main__":
    
    sys.excepthook = excepthook

    args = parse_arguments()

    config = load_config('kb0')

    kb_path = config['kb_config']['kb_path']

    if args.pdf_file:
        pdf_path = args.pdf_file
        if not os.path.exists(pdf_path):
            print(f"ERROR: File not found: {pdf_path}")
            sys.exit(1)
        md_path = f"{pdf_path}.md"
        pdf_to_text(pdf_path, md_path, args)
        sys.exit(1)

    activities_base = os.path.join(kb_path, "activities")

    if args.activity:
        search_dirs = [os.path.join(activities_base, args.activity, "raw")]
        for d in search_dirs:
            if not os.path.isdir(d):
                print(f"ERROR: Directory {d} does not exist.")
                sys.exit(1)
    else:
        search_dirs = [
            os.path.join(activities_base, name, "raw")
            for name in os.listdir(activities_base)
            if os.path.isdir(os.path.join(activities_base, name, "raw"))
        ]

    # Iterate through all files in the directory recursively
    for raw_dir in search_dirs:
        for root, dirs, files in os.walk(raw_dir):
            for file_name in files:
                if file_name.endswith(".pdf"):
                    pdf_path = os.path.join(root, file_name)
                    md_path = f"{pdf_path}.md"

                    # Skip if the text file already exists and --force is not specified
                    if not args.force and os.path.exists(md_path):
                        if args.v:
                            print(f"Skipping {md_path} (already exists). Use --force to overwrite.")
                        continue

                    pdf_to_text(pdf_path, md_path, args)

# import pdb; pdb.set_trace()
