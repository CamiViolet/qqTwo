# Script: copy_pdf_from_downloads.py
# Description: This script copies exported PDF from the Downloads directory to .\pdf.
#              The PDF files can be Polarion exports or any other PDF.
#
# Usage: python copy_pdf_from_downloads.py [<pattern>]
#
# Parameters:
#    <pattern> : (optional) specifies the PDF file to be taken from Downloads.


import json
import os
import re
import sys
import shutil


def excepthook(type, value, tb):
    import traceback, pdb
    traceback.print_exception (type, value, tb)
    print
    pdb.pm ()


def file_processing(pdf_file_list, filename_filter, config):
    pdf_import_dir = config['kb_config']['pdf_import_dir']

    for file_path in pdf_file_list:
        file_base_name = os.path.basename(file_path).lower()
        copy_it = False
        if "motionwise" in file_base_name:
            copy_it = True
        if filename_filter and filename_filter.lower() in file_base_name:
            copy_it = True
        if copy_it:
            dest_file = os.path.join(pdf_import_dir, os.path.basename(file_path))
            shutil.move(file_path, dest_file)
            print(f"Moved {os.path.basename(file_path)} to {os.path.dirname(dest_file)}")


# Load configuration from JSON file
def load_config(kb_name):
    
    config_file = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON syntax in configuration file: {config_file}")
        print(f"  Line {e.lineno}, Column {e.colno}: {e.msg}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load configuration file: {config_file}")
        print(f"  {type(e).__name__}: {e}")
        sys.exit(1)

    assert('kb_configs' in config)
    kb_configs = config['kb_configs']
    assert(kb_name in kb_configs)
    kb_config_path = kb_configs[kb_name]
    try:
        with open(kb_config_path, 'r', encoding='utf-8') as f:
            kb_config = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {kb_config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON syntax in configuration file: {kb_config_path}")
        print(f"  Line {e.lineno}, Column {e.colno}: {e.msg}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load configuration file: {kb_config_path}")
        print(f"  {type(e).__name__}: {e}")
        sys.exit(1)
    config['kb_config'] = kb_config

    return config


if __name__ == "__main__":
    sys.excepthook = excepthook

    filename_filter = None
    if len(sys.argv) > 1:
        filename_filter = sys.argv[1]

    config = load_config('kb0')

    # Create destination directory if it doesn't exist
    pdf_import_dir = config['kb_config']['pdf_import_dir']
    os.makedirs(pdf_import_dir, exist_ok=True)

    # Search for PDF files
    source_dir = config['source_dir']
    pdf_file_list = list()
    for filename in os.listdir(source_dir):
        if filename.lower().endswith('.pdf'):
            pdf_file_list.append(os.path.join(source_dir, filename))

    file_processing(pdf_file_list, filename_filter, config)

    # import pdb; pdb.set_trace()
