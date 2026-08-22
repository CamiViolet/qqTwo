"""
Script: copy_polarion_exports.py
Description: Copy Polarion export files from qpDoc to the qqOne knowledge base.

This script replicates the functionality of copying *.only_text.txt files
from the qpDoc txt_export directory to the knowledge base exports directory.

Usage: python copy_polarion_exports.py [<kb_name>]

Parameters:
   <kb_name> : (optional) specifies the knowledge base to use (default: kb0)
"""

import shutil
import os
import sys
import json
import argparse


def excepthook(type, value, tb):
    import traceback, pdb
    traceback.print_exception (type, value, tb)
    print
    pdb.pm ()


def copy_polarion_exports(config, args):
    """
    Copy Polarion export text files from source to destination.
    
    Copies all *.only_text.txt files from the qpDoc txt_export directory
    to the knowledge base exports txt_export directory, including subdirectories.
    """
    
    # Get source and destination from config
    source = config['polarion_txt_export_source']
    destination = config['polarion_txt_export_dest']
    
    # Create destination directory if it doesn't exist
    os.makedirs(destination, exist_ok=True)
    
    # Check if source exists
    if not os.path.exists(source):
        print(f"Warning: Source directory does not exist: {source}")
        return
    
    # Find all *.only_text.txt files recursively
    files_copied = 0
    for root, dirs, files in os.walk(source):
        for filename in files:
            if filename.endswith('.only_text.txt'):
                file_path = os.path.join(root, filename)
                
                # Calculate relative path to maintain directory structure
                relative_path = os.path.relpath(file_path, source)
                dest_file = os.path.join(destination, relative_path)
                
                # Create subdirectories in destination if needed
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                
                # Copy the file
                shutil.copy2(file_path, dest_file)
                if args.verbose:
                    print(f"Copied: {relative_path}")
                files_copied += 1
    
    print(f"\nTotal files copied from Polarion exports: {files_copied}")


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


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Copy Polarion export files from qpDoc to the qqOne knowledge base.'
    )
    parser.add_argument(
        'kb_name',
        nargs='?',
        default='kb0',
        help='Knowledge base to use (default: kb0)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.excepthook = excepthook
    
    args = parse_arguments()
    
    config = load_config(args.kb_name)
    copy_polarion_exports(config, args)
