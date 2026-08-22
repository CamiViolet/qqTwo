# Script: clean_1bf.py
# Description: Clean the 1bf (One Big File) e.g. by removing links, trailing spaces, empty lines, etc.
# Usage: python clean_1bf.py file_1bf
#
# Parameters:
#   file_1bf - Path to the 1bf file
#
# Examples:
#   python clean_1bf.py .\reports\component_1bf.txt

import os
import json
import re
import sys
from collections import defaultdict


filter_out = [
    "Skip to sidebar",
    "Skip to main content",
    "Skip to breadcrumbs",
    "Skip to search",
    "Linked Applications",
    "Edit View inline comments",
    "Save for later Watching Share",
]

def excepthook(type, value, tb):
    import traceback, pdb
    traceback.print_exception (type, value, tb)
    print
    pdb.pm ()


def main():
    sys.excepthook = excepthook
    
    file_1bf = sys.argv[1]

    with open(file_1bf, 'r', encoding='utf-8', errors='replace') as file:
        content = file.readlines()
    
    # Initialize output content
    out_content = ""
    
    # Process each line to remove trailing spaces and handle empty lines
    empty_line_count = 0
    
    for line in content:
        # Check if line contains any string from filter_out
        if any(filter_str in line for filter_str in filter_out):
            continue  # Skip this line

        # Skip specific lines
        if "dcdddInfdi" in line:
            continue
            
        clean_line = line.rstrip() + '\n'
        
        # Check if line is empty
        clean_line = clean_line.rstrip() + '\n'
        if clean_line.strip() == '':
            empty_line_count += 1
            if empty_line_count <= 1:
                out_content += clean_line
        else:
            # Non-empty line, reset counter and add the line
            empty_line_count = 0
            out_content += clean_line
    
    # Write the 1bf to a file
    with open(file_1bf, 'w', encoding='utf-8') as f:
        f.write(out_content)
    num_lines = len(out_content.splitlines())
    file_size = os.path.getsize(file_1bf)

if __name__ == "__main__":
    main()

# import pdb; pdb.set_trace()
