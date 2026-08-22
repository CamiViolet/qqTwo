# Script: manual_notes.py
# Description: Extract notes from the log file.
# Usage: python manual_notes.py source_file output_file
#
# Parameters:
#   source_file - Path to the file with manual notes
#   output_file - Path where the manual_notesd output will be written
#
# Examples:
#   python manual_notes.py .\exports\cookbook .\reports\component_1bf.txt

import os
import json
import re
import json
import os
import argparse
import sys
from library import normalize_to_C_symbol, load_config, excepthook
from collections import defaultdict


date_pattern = r'\b\d{2}[-/]\d{2}[-/]\d{4}\b'    # Example: 16/06/2026


def parse_arguments():
    parser = argparse.ArgumentParser(description="Convert PDF files to text.")
    parser.add_argument("pattern", help="Comma-separated list of regexes to search for")
    parser.add_argument("-o", "--output_file", help="File to be created")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose console output")
    return parser.parse_args()


if __name__ == "__main__":

    sys.excepthook = excepthook

    args = parse_arguments()

    config = load_config('kb0')

    kb_path = config['kb_config']['kb_path']
    
    patterns = [re.compile(p.strip(), re.IGNORECASE) for p in args.pattern.split(',')]
    log_file = config['kb_config']['log_file']

    output_file = args.output_file
    
    out_content = ""
    
    # Read the source file and find lines containing the tag
    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
        

    seen_sections = set()

    def line_indent(line):
        return len(line) - len(line.lstrip())

    def section_bounds(match_index):
        start = match_index
        if line_indent(lines[start]) > 0:
            while start > 0:
                previous_line = lines[start - 1]
                start -= 1
                if previous_line.strip() and line_indent(previous_line) == 0:
                    break

        if start>0:
            date_line = lines[start - 1]
            if line_indent(date_line) == 0:
                if re.search(date_pattern, date_line):
                    start -= 1

        end = match_index + 1
        while end < len(lines):
            current_line = lines[end]
            if current_line.strip() and line_indent(current_line) == 0:
                break
            end += 1

        return start, end

    # Add dates to sections that don't have them
    lines2 = []
    current_date = None
    for index, line in enumerate(lines):
        if line.strip() and line_indent(line) == 0:
            if re.search(date_pattern, line):
                current_date = line.strip()
                current_date_index = index
            else:
                if current_date:
                    if (index-1) != current_date_index: # line has no date
                        lines2.append(current_date + '\n')
        lines2.append(line)
    lines = lines2

    for index, line in enumerate(lines):
        if not any(p.search(line) for p in patterns):
            continue

        start, end = section_bounds(index)
        if (start, end) in seen_sections:
            continue
        
        seen_sections.add((start, end))
        section_text = ''.join(lines[start:end])
        if out_content and not out_content.endswith('\n'):
            out_content += '\n'
        out_content += section_text
    
    # Write the output to a file
    with open(output_file, 'w', encoding='utf-8', errors='replace') as f:
        f.write(out_content)
    # print(f"Created '{output_file}' with {len(collected_sections)} sections")



# import pdb; pdb.set_trace()
