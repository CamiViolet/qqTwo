"""
Script to convert a .docx file to a plain text file.
Usage: python docx_to_txt.py <input_dir> <output_dir>
"""

import json
import sys
import os
from docx import Document
import zipfile

def excepthook(type, value, tb):
    import traceback, pdb
    traceback.print_exception (type, value, tb)
    print
    pdb.pm ()


def docx_to_txt(docx_input):
    """
    Read all .docx files from a directory and export their content to .txt files.
    
    Args:
        input_dir (str): Directory containing the input .docx files
    """
    
    # Find all .docx files in the input directory and subfolders (recursive)
    docx_files = []
    for root, dirs, files in os.walk(docx_input):
        for f in files:
            if f.endswith('.docx'):
                docx_files.append(os.path.join(root, f))
    
    print(f"Found {len(docx_files)} .docx file(s) to convert...")
    
    # Process each .docx file
    for docx_path in docx_files:
        txt_path = os.path.splitext(docx_path)[0] + '.txt'
        
        # Load the .docx file
        doc = Document(docx_path)
        
        # Extract text from all paragraphs
        full_text = []
        for paragraph in doc.paragraphs:
            full_text.append(paragraph.text)
        
        # Join paragraphs with newlines
        content = '\n'.join(full_text)
        
        # Write to text file
        with open(txt_path, 'w', encoding='utf-8') as txt_file_obj:
            txt_file_obj.write(content)
    
    print(f"\nSuccessfully converted {len(docx_files)} file(s)")


# Load configuration from JSON file
def load_config():
    config_file = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


if __name__ == "__main__":
    sys.excepthook = excepthook

    config = load_config()

    docx_input = config.get("docx_input")

    zip_files = []
    for f in os.listdir(docx_input):
        if f.endswith('.zip') and os.path.isfile(os.path.join(docx_input, f)):
            zip_files.append(os.path.join(docx_input, f))    

    assert(len(zip_files) == 1)

    # Unzip the file in the same directory as the zip file
    zip_path = zip_files[0]
    extract_dir = os.path.dirname(zip_path)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    print(f"Extracted {zip_path} to {extract_dir}")

    docx_to_txt(docx_input)


# import pdb; pdb.set_trace()

