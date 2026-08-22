# Script: update_confluence_pages.py
# Description: 
# Usage: 
#
# Parameters:
#
# Examples:
#   python update_confluence_pages.py --file_name Our_process_an_analysis.txt
#   python update_confluence_pages.py --web_page https://confluence.tttech.com/spaces/TTTAMP/pages/793347575/ASPICE+View


import argparse
from getpass import getpass
import json
import os
import re
from pyparsing import line
import requests
import sys
import zlib
from bs4 import BeautifulSoup, NavigableString, Tag
from urllib.parse import urljoin, urlparse
from datetime import datetime
from web_to_markdown import fetch_web_page, fetch_confluence_page
from dotenv import load_dotenv

CONFLUENCE_HOST = 'confluence.tttech.com'

global password

password = None


def excepthook(type, value, tb):
    import traceback, pdb
    traceback.print_exception (type, value, tb)
    print
    pdb.pm ()
    
    
def clean_up_the_content(content):
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if len(line) > 200:
            # Skip lines with very low compression ratio (e.g. binalry content)
            # original_size = len(line.encode('utf-8'))
            # compressed = zlib.compress(line.encode('utf-8'), level=1)
            # compressed_size = len(compressed)
            # compression_ratio = compressed_size / original_size
            # if compression_ratio < 0.5:
            #     import pdb; pdb.set_trace()
            #     continue
            
            # Skip lines with very few spaces
            space_ratio = line.count(' ') / len(line)
            if space_ratio < 0.05:
                continue
        cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)


def create_valid_filename(page_name, jira_issue_id = None):
    file_name = page_name

    file_name = file_name.encode('ascii', 'ignore').decode('ascii')
    
    file_name = file_name.replace(" ", "_").replace("\\", "_").replace("/", "_").replace(":", "_")
    file_name = file_name.replace(")", "_").replace("(", "_").replace(",", "_").replace("+", "_")
    file_name = file_name.replace("[", "_").replace("]", "_")
    file_name = file_name.replace("{", "_").replace("}", "_")

    if jira_issue_id:
        file_name = jira_issue_id + '_' + file_name

    while "__" in file_name:
        file_name = file_name.replace("__", "_")
        
    return(file_name)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Update Confluence pages from local files")
    parser.add_argument(
        '--file_name',
        type=str,
        default=None,
        help="Update a single file instead of the entire confluence directory"
    )
    parser.add_argument(
        '--web_page',
        type=str,
        default=None,
        help="Download a single web page"
    )
    return parser.parse_args()


def get_file_properties(lines):
    properties = {}
    for i, line in enumerate(lines):
        if i>20:
            break
        line = line.strip()
        regex = "([ a-zA-Z]+)\s*:(.*)"
        match = re.match(regex, line)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            if key=='TCAG users':
                continue
            properties[key] = value
    return properties


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


def main():
    global password

    sys.excepthook = excepthook

    args = parse_arguments()

    load_dotenv()
    
    CONFIG = load_config('kb0')
    
    if args.web_page:
        url = args.web_page
        parsed = urlparse(url)
        if parsed.hostname == CONFLUENCE_HOST:

            if not password:
                password = getpass("Enter the password: ")
            import pdb; pdb.set_trace()
            content  = fetch_confluence_page(url, os.environ.get('USER', ''), password)
        else:
            content = fetch_web_page(url)
        
        file_path = r"C:\Dev_Analisys\qqone\page.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Updated page: {file_path}")
        return
    
    import pdb; pdb.set_trace()

    updated = False
    confluence_dir = CONFIG['kb_config']['confluence']
    for root, dirs, files in os.walk(confluence_dir):
        for file in files:
            if args.file_name and file != args.file_name:
                continue
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.readlines()
                except UnicodeDecodeError as e:
                    print(f"UTF-8 decode failed for {file_path}: {e}. Retrying with latin-1.")
                    try:
                        with open(file_path, 'r', encoding='latin-1') as f:
                            content = f.readlines()
                    except Exception as inner_e:
                        print(f"Error reading file {file_path} with fallback encoding: {inner_e}")
                        continue
                except IOError as e:
                    print(f"Error reading file {file_path}: {e}")
                    continue
                file_props = get_file_properties(content)

                if 'Page URL' not in file_props:
                    continue
                url = file_props['Page URL']
                # if 'confluence.tttech.com' not in url:
                #     continue
                parsed = urlparse(url)
                if parsed.hostname != CONFLUENCE_HOST:
                    raise ValueError(f"Refusing to send credentials to untrusted host: {parsed.hostname}")
                import pdb; pdb.set_trace()
                # title, modified_on, new_content = fetch_confluence_page(url)
                if not new_content:
                    continue
                if modified_on:
                    file_props['Page Modified On'] = modified_on
                title = title.replace(" - Confluence", "")
                title = title.replace(" - TTTech Auto - BU Safety Products", "")
                
                new_content = clean_up_the_content(new_content)

                props_to_str = ""
                for key, value in file_props.items():
                    props_to_str += f"{key}: {value}\n\n"

                new_content = props_to_str + '\n' + new_content

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                updated = True
                print(f"Updated page: {title}")

    if not updated:
        print("No pages were updated.")


if __name__ == "__main__":
    main()

# import pdb; pdb.set_trace()
