# Script: smart_copy.py
# Description: Copy a part of a content of a file.
# Usage: python smart_copy.py input_file output_file
#
# Parameters:
#   input_file
#   output_file
#   regex_start
#   regex_end
#
# Examples:
#   python smart_copy.py .\exports\cookbook .\reports\component_1bf.txt

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
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    regex_start = sys.argv[3]
    regex_end = sys.argv[4]
    
    # Load the content of input_file
    with open(input_file, 'r', encoding='utf-8') as f:
        in_content = f.read()
    
    out_content = []
    copying = False
    for line in in_content.splitlines(keepends=True):
        if not copying and re.search(regex_start, line):
            copying = True
        if copying:
            if re.search(regex_end, line):
                break
            out_content.append(line)
    out_content = ''.join(out_content)

    # Write the 1bf to a file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(out_content)
    print(f"Created '{output_file}'")

if __name__ == "__main__":
    main()

# import pdb; pdb.set_trace()
