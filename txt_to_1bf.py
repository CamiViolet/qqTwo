"""
Script to concatenate all .txt files in a directory into a single file.
Usage: python txt_to_1bf.py <input_dir>
"""

import sys
import os
from docx import Document

def excepthook(type, value, tb):
    import traceback, pdb
    traceback.print_exception (type, value, tb)
    print
    pdb.pm ()


def txt_to_1bf(input_dir):
    """
    Read all .txt files from a directory and concatenate them into a single file.
    
    Args:
        input_dir (str): Directory containing the input .txt files
    """

    output_dir = input_dir.replace("_txt", "") + "_1bf"     # Directory where the output file will be saved
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Find all .txt files in the input directory (no recursion)
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt') and os.path.isfile(os.path.join(input_dir, f))]

    # Find all .txt files in the input directory (no recursion)
    txt_files = [f for f in txt_files if not f[0].isdigit() or int(os.path.basename(f)[:4]) >= 2020]
    
    print(f"Found {len(txt_files)} .txt file(s) to concatenate...")
    
    # Sort files for consistent ordering
    txt_files.sort(reverse=True)
    
    # Concatenate all text files
    all_content = []
    all_content.append(f"\nL'autore di queste note sono io, Carlo.\n\n")
    for txt_file in txt_files:
        txt_path = os.path.join(input_dir, txt_file)
        
        # Read the .txt file
        with open(txt_path, 'r', encoding='utf-8') as file:
            content = file.read()
            # Add filename separator before content
            all_content.append(f"\nFile: {txt_file}\n\n{content}")
    
    # Join all content with double newlines between files
    concatenated_content = '\n\n'.join(all_content)
    
    # Create output filename based on input directory name
    dir_name = os.path.basename(input_dir.rstrip(os.sep)).replace("_txt", "")
    output_file = os.path.join(output_dir, f"{dir_name}.1bf.txt")
    
    # Write to single output file
    with open(output_file, 'w', encoding='utf-8') as output:
        output.write(concatenated_content)
    
    print(f"\nSuccessfully concatenated {len(txt_files)} file(s) into '{output_file}'")


if __name__ == "__main__":
    sys.excepthook = excepthook

    input_directory = r"C:\Dev_TTT\DTech-20251226T145049Z-3-001\DTech_txt"
    txt_to_1bf(input_directory)

# import pdb; pdb.set_trace()
