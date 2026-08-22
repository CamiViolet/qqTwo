# Script: concatenate.py
# Description: Concatenate files from a folder to compose the 1bf (One Big File).
# Usage: python concatenate.py source_path output_file
#
# Parameters:
#   source_path - Path to the folder containing the files to be concatenated
#   output_file - Path where the concatenated output will be written
#
# Examples:
#   python concatenate.py .\exports\cookbook .\reports\component_1bf.txt

import os
import json
import re
import sys
from collections import defaultdict


def excepthook(type, value, tb):
    import traceback, pdb
    traceback.print_exception (type, value, tb)
    print
    pdb.pm ()


def main():
    sys.excepthook = excepthook
    
    source_path = sys.argv[1]
    extensions  = sys.argv[2]   # comma-separated list of file extensions, example: .txt,.md
    output_file = sys.argv[3]
    
    # Parse extensions into a list
    ext_list = [ext.strip().lower() for ext in extensions.split(',')]
    
    filter_out = [
        "Skip to sidebar",
        "Skip to main content",
        "Skip to breadcrumbs",
        "Skip to search",
        "Linked Applications",
        "Confluence",
        "Spaces",
        "Analytics",
        "Create",
        "Search",
        "Help",
        "Configure",
        "Edit View inline comments",
        "Save for later Watching Share",
    ]
    
    out_content = ""
    
    # Recursively find all files in source_path and subdirectories
    all_files = []
    for root, dirs, files in os.walk(source_path):
        for file_name in files:
            # Check if file has one of the specified extensions
            if any(file_name.lower().endswith(ext) for ext in ext_list):
                all_files.append(os.path.join(root, file_name))
    
    print(f"Found {len(all_files)} files in '{source_path}'")
    
    for file_path in all_files:
        # Get relative path for display in file header
        relative_path = os.path.relpath(file_path, source_path)
        
        # Check if it's a file (not a directory)
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.readlines()
                
                # Filter out unwanted lines
                filtered_content = []
                for line in content:
                    stripped_line = line.strip()
                    if not any(filter_str in stripped_line for filter_str in filter_out):
                        filtered_content.append(line)
                
                # Format the filtered content with indentation and trimmed spaces
                formatted_content = []
                for line in filtered_content:
                    formatted_line = ('    ' + line).rstrip() + '\n'
                    formatted_content.append(formatted_line)
                
                # Add file header and formatted content to output
                file_header = f"\n\n# File: {relative_path}\n"
                formatted_content = ''.join(formatted_content)
                while '\n\n\n' in formatted_content:
                    formatted_content = formatted_content.replace('\n\n\n', '\n\n')
                    
                out_content += file_header + formatted_content + '\n'

    # Write the 1bf to a file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(out_content)
    print(f"Created '{output_file}'")

if __name__ == "__main__":
    main()

# import pdb; pdb.set_trace()
