# Script: compress_1bf.py
# Description: Reduce the size of a 1bf (One Big File) by removing dupliacated blocks.
# Usage: python compress_1bf.py file_1bf
#
# Parameters:
#   file_1bf - Path to the 1bf file
#
# Examples:
#   python compress_1bf.py .\reports\component_1bf.txt

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
    
    file_1bf = sys.argv[1]

    with open(file_1bf, 'r', encoding='utf-8', errors='replace') as file:
        content = file.readlines()

    out_content = [{
        'text': line,
        'hash': hash(line.strip())
    } for line in content]

    for idx, item in enumerate(out_content):
        # if item['text'].strip() == '':
        #     import pdb; pdb.set_trace()
        if item['hash'] is None or len(item['text'])<80:
            continue
        for j in range(idx + 100, len(out_content)):
            if out_content[j]['hash'] is None or len(out_content[j]['text'])<80:
                continue
            other_item = out_content[j]
            if item['hash'] == other_item['hash']:
                out_content[j]['hash'] = None  # Mark as duplicate 

    # Write the 1bf to a file
    output_lines = [item['text'] for item in out_content if item['hash'] is not None]
    with open(file_1bf, 'w', encoding='utf-8') as f:
        f.writelines(output_lines)
    file_size = os.path.getsize(file_1bf)

if __name__ == "__main__":
    main()

# import pdb; pdb.set_trace()
