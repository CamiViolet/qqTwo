'''
usage: update.py [-h] [-v] [-vv] [activity_name]

Generate the 1bf (One Big File) for all the activities

positional arguments:
  activity_name  Generate the 1bf only for the specified topic (default: all activities)

options:
  -h, --help  show this help message and exit
  -v          Verbose console output
  -vv         Very Verbose console output

Example:
    python update.py --network sprtorcas_1613_security_concept_for_dds_com_tlc
  '''

import argparse
from getpass import getpass
import json
import glob
import fitz  # pip install PyMuPDF
import os
import re
import sys
from collections import defaultdict
from library import load_json, doc_properties, load_config, excepthook
from web_to_markdown import fetch_web_page, fetch_confluence_page
from dotenv import load_dotenv
import yaml
import importlib

global config, password

password = None


def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate the 1bf (One Big File) for all the activities")
    parser.add_argument("activity_name", nargs="?", default=None, help="Generate the 1bf only for the specified topic (default: all activities)")
    parser.add_argument("-v", action="store_true", help="Verbose console output")
    parser.add_argument("-vv", action="store_true", help="Very Verbose console output")
    parser.add_argument("--network", action="store_true", help="Allows fetching web pages (disabled by default for performance reasons)")
    parser.add_argument("--split_chapters", action="store_true", help="Split output by chapters (detected by heading level 1).")

    return parser.parse_args()


def pdf_to_md(pdf_file, args):
    """
    Converts a PDF file to a markdown file.

    :param pdf_file: Path to the input PDF file.
    :param md_path: Path to the output markdown file.
    """
    
    md_path = f"{pdf_file}.md"
    
    # Open the PDF file
    pdf_document = fitz.open(pdf_file)

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
            chapter_md_path = f"{pdf_file}.chapter_{chapter_idx}_{title_normalized}.md"
            with open(chapter_md_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write("\n".join(lines))
            print(f"PDF exported to: {chapter_md_path}")

    with open(md_path, 'w', encoding='utf-8') as txt_file:

        # Write the text to the file
        txt_file.write("\n".join(full_text))

    print(f"PDF exported to: {md_path}")


def xlsx_to_md(xlsx_path):
    load_workbook = importlib.import_module("openpyxl").load_workbook

    def normalize_cell(value):
        if value is None:
            return ""
        text = str(value).strip()
        text = text.replace("\n", "<br>")
        return text.replace("|", "\\|")

    def worksheet_to_md(worksheet):
        rows = []
        max_columns = 0

        for row in worksheet.iter_rows(values_only=True):
            normalized = [normalize_cell(cell) for cell in row]
            rows.append(normalized)
            max_columns = max(max_columns, len(normalized))

        if max_columns == 0:
            return ""

        # Normalize row lengths so markdown table columns stay aligned.
        normalized_rows = [row + [""] * (max_columns - len(row)) for row in rows]

        # Use the first non-empty row as header, otherwise create empty headers.
        header = [""] * max_columns
        data_start = 0
        for index, row in enumerate(normalized_rows):
            if any(cell != "" for cell in row):
                header = row
                data_start = index + 1
                break

        lines = []
        lines.append("| " + " | ".join(header) + " |")
        lines.append("| " + " | ".join(["---"] * max_columns) + " |")

        for row in normalized_rows[data_start:]:
            lines.append("| " + " | ".join(row) + " |")

        return "\n".join(lines)

    workbook = load_workbook(xlsx_path, data_only=True)
    markdown_sections = []

    for sheet_name in workbook.sheetnames:
        worksheet = workbook[sheet_name]
        markdown_sections.append(f"## {sheet_name}")
        table_md = worksheet_to_md(worksheet)
        if table_md:
            markdown_sections.append(table_md)
        else:
            markdown_sections.append("(empty sheet)")

    md_path = f"{xlsx_path}.md"
    with open(md_path, "w", encoding="utf-8") as md_file:
        md_file.write("\n\n".join(markdown_sections) + "\n")

    return md_path


def main():
    global config
    
    sys.excepthook = excepthook

    args = parse_arguments()

    load_dotenv()

    config = load_config('kb0')

    kb_path = config['kb_config']['kb_path']

    search_path = kb_path
    if args.activity_name:
        search_path = os.path.join(kb_path, 'activities', args.activity_name)

    if not os.path.isdir(search_path):
        print(f"Error: activity '{args.activity_name}' does not exist in the knowledge base.")
        return
    
    xlsx_files = glob.glob(os.path.join(search_path, "**", "*.xlsx"), recursive=True)
    for xlsx_file in xlsx_files:
        xlsx_to_md(xlsx_file)
    
    pdf_files = glob.glob(os.path.join(search_path, "**", "*.pdf"), recursive=True)
    for pdf_file in pdf_files:
        pdf_to_md(pdf_file, args)

    return


if __name__ == "__main__":
    main()

# import pdb; pdb.set_trace()
