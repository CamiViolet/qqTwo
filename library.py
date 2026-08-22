# Script: library.py
#
# Description: Collection of helpers functions.

import argparse
import itertools
import json
import glob
import os
import re
import sys
from collections import defaultdict


DOC_PROPERTIES_MAX_LINES = 30


def calculate_markdown_size(directory):
    """Calculate the total size of all markdown files in a directory.
    
    Given a path to an activity directory, this function recursively sums up
    the size of all markdown files (.md) within that directory.
    
    Args:
        directory: Path to the activity directory
        
    Returns:
        Total size in bytes of all markdown files in the directory
    """
    total_size = 0
    try:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.md') and file.lower() != 'glossary.md':
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except OSError:
                        pass  # Skip files that can't be accessed
    except OSError:
        pass  # Return 0 if directory can't be accessed
    return total_size


def get_activity_update(activity):
    """Get the most recent update date for an activity"""
    md_files = glob.glob(os.path.join(activity, "*.md"))
    dates = []
    for file in md_files:
        doc_properties = get_doc_properties2(file)
        updated = doc_properties.get('max_date')
        if updated:
            dates.append(updated)
    return max(dates) if dates else None


def get_prop_names():
    prop_names = [
        'alternatives', # The topic described in the document has these alternatives
        'author', 
        'confluence_page_id', 
        'context',      # These words are used to narrow down the context of the document
        'created', 
        'date', 
        'keywords',     # The document is specifically about these keywords
        'modified', 
        'published', 
        'related',      # The document is somehow related to these words
        'source', 
        'synonyms',     # These words are interchangeable
        'title', 
        'updated'
    ]
    return prop_names


def get_prop_names_for_dates():
    prop_names = get_prop_names()
    prop_names_for_dates = ['created', 'date', 'modified', 'published', 'updated']
    assert set(prop_names_for_dates).issubset(set(prop_names))
    return prop_names_for_dates


def excepthook(type, value, tb):
    import traceback, pdb
    traceback.print_exception (type, value, tb)
    print
    pdb.pm ()


def get_doc_properties(lines):
    """
    Search for properties in the first lines of the document.
    Parameter: list of lines

    Examples of lines with properties:
    Keywords: AI
    Related: "data science", AI, ML, "deep-learning"
    Synonyms: "AI", 'artificial intelligence'
    """
    if type(lines) == str:
        lines = lines.splitlines()
    properties = {}
    prop_names = get_prop_names()
    prop_names_for_dates = get_prop_names_for_dates()
    for i, line in enumerate(lines):
        if i>DOC_PROPERTIES_MAX_LINES:    # Search for properties only in the first lines of the document
            break
        line = line.strip()
        if ':' not in line:
            continue
        if line.startswith("- "):
            line = line[1:].strip()
        prop_name = line[:line.index(':')].strip().lower()
        if prop_name not in prop_names:
            continue
        props = line[line.index(':')+1:].strip()    # Example: "data science", AI, ML, "deep-learning"
        props = props.split(",")
        props = [p.strip().strip('"').strip("'").strip() for p in props]
        props = [p for p in props if p]

        # Normalize dates to YYYY-MM-DD
        if prop_name in prop_names_for_dates:
            new_props = []
            for p in props:
                p = p.replace('/', '-')
                p = p.replace('.', '-')
                p = re.sub(r'^(\d{2})-(\d{2})-(\d{4})\s+(\d{2}:\d{2})$', r'\3-\2-\1 \4', p)
                p = re.sub(r'^(\d{2})-(\d{2})-(\d{4})$', r'\3-\2-\1', p)
                new_props.append(p)
            props = new_props

        if props:
            properties[prop_name] = props

    dates = [properties[prop_name] for prop_name in prop_names_for_dates if prop_name in properties]
    dates = [date for sublist in dates for date in sublist]
    if dates:
        properties['max_date'] = max(dates)

    return properties


def get_doc_properties2(file_path):
    '''
    Search for properties in the first lines of the document.
    Parameter: file path
    '''
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content_list = list(itertools.islice(f, DOC_PROPERTIES_MAX_LINES + 1))
    return get_doc_properties(content_list)


def filter_out_properties(lines):
    lines_new = []
    for i, line in enumerate(lines):
        if i>DOC_PROPERTIES_MAX_LINES:    # Search for properties only in the first lines of the document
            lines_new.append(line)
            continue
        line = line.strip()
        if ':' not in line:
            lines_new.append(line)
            continue
        if line.startswith("- "):
            line = line[1:].strip()
        prop_name = line[:line.index(':')].strip().lower()
        if prop_name not in prop_names:
            lines_new.append(line)
            continue
    return lines_new


def print_results_to_console(prev_results):
    if prev_results is None:
        return
    i = 0
    with open(r"C:\Users\nxg18988\AppData\Local\Temp\console.txt", "w") as fl:
        for finding in prev_results:
            line = "%s: %s (%s kB)" % (i, finding['title'], int(finding['size']/1024))
            if 'count' in finding:
                line += " [%d matches]" % finding['count']
            print(line)
            fl.write(line + "\n")
            i += 1


def write_file_with_properties(file_path, properties, lines):
    if type(lines) == str:
        lines = lines.splitlines()
    lines = filter_out_properties(lines)
    # import pdb; pdb.set_trace()
    with open(file_path, 'w', encoding='utf-8') as f:
        for prop_name, props in sorted(properties.items()):
            line = f"{prop_name}: {', '.join(props)}\n"
            f.write(line)
        f.write('\n')
        f.writelines(lines)


# Load local configuration and the configuration of the specified knowledge base
def load_config():

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

    current_knowledge_base = config.get('current_knowledge_base')

    assert('kb_configs' in config)
    kb_configs = config['kb_configs']
    assert(current_knowledge_base in kb_configs)
    config['kb_path'] = kb_configs[current_knowledge_base]['path']
    kb_config_path = os.path.join(kb_configs[current_knowledge_base]['path'], 'config.json')
    try:
        with open(kb_config_path, 'r', encoding='utf-8') as f:
            kb_config = json.load(f)
            kb_config['kb_path'] = os.path.dirname(kb_config_path)
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


# Load JSON file
def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        try:
            content = json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR parsing JSON file '{path}': {e}")
            sys.exit(1)
    return content


def normalize_to_C_symbol(word):
    """
    Replace any character that is not alphanumeric or underscore with underscore
    """
    norm_kw = re.sub(r'[^a-zA-Z0-9_]', '_', word)
    
    while "__" in norm_kw:
        norm_kw = norm_kw.replace("__", "_")
    
    return(norm_kw)


def normalize_to_filename(name):
    """
    Translate any string to a valid file name (without extension).
    Characters not allowed in Windows or Linux file names are replaced with underscore.
    Consecutive underscores and consecutive spaces are collapsed.
    Works on both Windows and Linux.
    """
    normalized = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '_', name)

    while '__' in normalized:
        normalized = normalized.replace('__', '_')

    while '  ' in normalized:
        normalized = normalized.replace('  ', ' ')

    normalized = normalized.strip('_ ')

    return normalized


def search_for_file(directory, filename):
    """
    Searches for a file with the given filename in the specified directory and its subdirectories.

    Args:
        directory (str): The directory to start the search from.
        filename (str): The name of the file to search for.

    Returns:
        str: The full path of the file if found, otherwise None.
    """
    for root, dirs, files in os.walk(directory):
        if filename in files:
            return os.path.join(root, filename)
    return None


def doc_properties(files):
    """
    Get the properties of each file.
    Returns a dictionary with file names as keys and the properties as value.
    """
    properties = defaultdict(dict)
    for file in files:
        with open(file, 'r', encoding='utf-8', errors='replace') as f:
            content_list = f.readlines()
            content = ('\n').join(content_list)
            if "Analytics" in content and "Powered by Atlassian Confluence" in content:
                properties[file]['file_type'] = "Confluence Page"
    return properties


def parse_arguments():
    parser = argparse.ArgumentParser(description="Create a dynamic context by using the input parameter.")
    parser.add_argument("-v", action="store_true", help="Verbose console output")
    parser.add_argument("-vv", action="store_true", help="Very Verbose console output")

    return parser.parse_args()

# import pdb; pdb.set_trace()
