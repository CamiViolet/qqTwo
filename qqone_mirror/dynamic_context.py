# Script: dynamic_context.py
# Description: Create a dynamic context (1bf - One Big File).
# Usage: python dynamic_context.py pattern
#
# Parameters:
#   pattern - String to be searched (regex)
#
# Examples:
#   python dynamic_context.py -L1 "smoke.?test" 100
#   python dynamic_context.py "what is a concept design document?" -p concept.design --path cookbook\relevant_0.gitignore

import argparse
import clean_1bf
import compress_1bf
from datetime import datetime, timedelta
import glob
import json
from library import get_activity_date
import os
import pyperclip
import re
import sys
from collections import defaultdict
# from get_patterns import get_patterns
from dotenv import load_dotenv

CONFIG = None


# Load environment variables from .env file
load_dotenv()
TEMPORARY_DIR = os.getenv("TEMPORARY_DIR")
if not TEMPORARY_DIR:
    TEMPORARY_DIR = os.environ.get('TEMP')
if not TEMPORARY_DIR:
    TEMPORARY_DIR = os.path.dirname(__file__)


def excepthook(type, value, tb):
    import traceback, pdb
    traceback.print_exception (type, value, tb)
    print
    pdb.pm ()


def collect_context_by_content(files, regex_list, len_out_content_1, context_max_size, doc_props, args):
    """
    Collect context by searching for regex matches within file contents, using a window mechanism.
    Returns out_content
    """

    if args.sfc:
        return ""
    
    # window_radius defines the number of lines to include before and after each pattern match,
    # setting the size of the contextual window extracted around every occurrence.
    window_radius = 400

    max_iterations = 5

    iteration = 0
    while True:
        cumulative_out_content = ""
        files_count = 0
        for file in files:
            file_name = os.path.basename(file)
            file_name_matching = any(regex.search(file_name) for regex in regex_list)
            if not file_name_matching:
                with open(file, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.readlines()
                    content = [line.rstrip('\n') for line in content]
                    # Extract context windows around regex matches in content
                    windows_content, occurrences = extract_context_windows(content, regex_list, window_radius)
                    original_size = os.path.getsize(file)
                    density = int(1_000_000 * occurrences / original_size) if original_size else 0
                    if occurrences:
                        cumulative_out_content = cumulative_out_content + f"\nFile: (by content) {file_name}\n\n" + windows_content
                        files_count += 1
                        if args.vv:
                            print(f"By content: file:{file} occurrences:{occurrences} original_size:{original_size} extracted_context_size:{len(windows_content)} density:{density} occurrences/MB")
        if args.v or args.vv:
            print(f"By content (iteration {iteration}): window_radius:{window_radius} files_count:{files_count} context_size:{len(cumulative_out_content) / 1024:.1f} kB")
        context_size = len_out_content_1 + len(cumulative_out_content)
        if context_size > 10*context_max_size:
            print(f"ERROR: too many matches. Please refine the search patterns.")
            return None
            
        if context_size <= context_max_size:
            break   # This is good
        if iteration >= (max_iterations-1):
            break   # This is not good

        window_radius = int(window_radius / 2)
        iteration += 1

    return cumulative_out_content


def collect_context_by_filename(files, regex_list, doc_props, args):
    """
    Collect context by matching file names against regex_list.
    Returns (out_content)
    """
    global CONFIG
    
    if args.r:
        return ""
    
    if args.sfn:
        return ""

    if not args.patterns:
        # Load the words.json file
        keywords_file = CONFIG['kb_config']['keywords_file']
        with open(keywords_file, 'r', encoding='utf-8') as f:
            keywords = json.load(f)     # Such words are lower case and singular
        keywords_max_freq = next(iter(keywords.items()))[1]

        # Load the ngrams.json file
        ngrams_file = CONFIG['kb_config']['ngrams_file']
        with open(ngrams_file, 'r', encoding='utf-8') as f:
            common_ngrams = json.load(f)     # Such words are lower case and singular
        common_ngrams_max_freq = next(iter(common_ngrams.items()))[1]

    cumulative_out_content = ""  # Selected content by file name
    files_count = 0
    score = dict()
    for file in files:
        file_name = os.path.basename(file)
        file_name_matching = any(regex.search(file_name) for regex in regex_list)
        score[file] = 0
        if not args.patterns:
            for regex in regex_list:
                if regex.search(file_name):
                    frequency = keywords.get(regex.pattern, 0)
                    if frequency:
                        score[file] += frequency/keywords_max_freq
                    frequency = common_ngrams.get(regex.pattern, 0)
                    if frequency:
                        score[file] += frequency/common_ngrams_max_freq
        if file_name_matching:  # Check if the file name matches any regex
            # If the file name matches the regex, then get the full content of the file
            if args.v:
                print(f"Matching file name: {file_name} (score:{score[file]})")
            if args.vv:
                print(f"Matching file path: {file}")
            with open(file, 'r', encoding='utf-8', errors='replace') as f:
                files_count += 1
                file_type = doc_props.get(file, {}).get('file_type')
                file_type_str = ""
                if file_type:
                    file_type_str = f"File Type: {file_type}\n\n"
                cumulative_out_content = f"\nFile: (by name) {file_name}\n\n{file_type_str}" \
                    + f.read() \
                    + cumulative_out_content    # The content of the file is put in front of the dynamic context
    if args.v or args.vv:
        print(f"By file name: files_count:{files_count} context_size:{len(cumulative_out_content) / 1024:.1f} kB")
    return cumulative_out_content


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


def extract_context_windows(content, regex_list, window_radius):
    """
    Extracts context windows around regex matches in content.
    Returns (out_content, occurrences)
    """
    processed_ranges = []
    out_content = ""
    occurrences = 0
    for i, line in enumerate(content):
        if any(regex.search(line) for regex in regex_list):
            occurrences += 1
            start = max(0, i - window_radius)
            end = min(len(content), i + window_radius + 1)
            for r in processed_ranges:
                if start < r[1]:
                    start = r[1]
            if start >= end:
                continue
            processed_ranges.append((start, end))
            scope = content[start:end]
            out_content += '\n'.join(scope)
    return out_content, occurrences


# Load configuration from JSON file
def load_config(kb_name):
    
    config_file = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {config_file}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON syntax in configuration file: {config_file}")
        print(f"  Line {e.lineno}, Column {e.colno}: {e.msg}")
        return None
    except Exception as e:
        print(f"ERROR: Failed to load configuration file: {config_file}")
        print(f"  {type(e).__name__}: {e}")
        return None

    assert('kb_configs' in config)
    kb_configs = config['kb_configs']
    assert(kb_name in kb_configs)
    kb_config_path = kb_configs[kb_name]
    config['kb_path'] = os.path.dirname(kb_config_path)
    try:
        with open(kb_config_path, 'r', encoding='utf-8') as f:
            kb_config = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {kb_config_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON syntax in configuration file: {kb_config_path}")
        print(f"  Line {e.lineno}, Column {e.colno}: {e.msg}")
        return None
    except Exception as e:
        print(f"ERROR: Failed to load configuration file: {kb_config_path}")
        print(f"  {type(e).__name__}: {e}")
        return None
    config['kb_config'] = kb_config

    return config


def reduce_context_size(encoded, context_max_size, regex_list, args):
    # window_radius defines the number of lines to include before and after each pattern match,
    # setting the size of the contextual window extracted around every occurrence.
    window_radius = 400

    max_iterations = 7

    decoded = encoded.decode('utf-8', errors='ignore')
    content = decoded.splitlines()
    iteration = 0
    while True:
        # Extract context windows around regex matches in content
        out_content, occurrences = extract_context_windows(content, regex_list, window_radius)
        if args.v or args.vv:
            print(f"By content (recurse) (iteration {iteration}): occurrences:{occurrences} original_size:{len(content)} window_radius:{window_radius} context_size:{len(out_content) / 1024:.1f} kB")
        if len(out_content) <= context_max_size:
            break   # This is good
        if iteration >= (max_iterations-1):
            break   # This is not good

        window_radius = int(window_radius / 2)
        iteration += 1

    return out_content.encode('utf-8')


def parse_arguments(cmd_line_args):
    parser = argparse.ArgumentParser(
        prog='aid',
        description="(AI Dynamic) Ask questions to the knowledge base.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            '  aid "who is carlo?"\n'
            '  aid "review in polarion" -p review,polarion -l\n'
        ),
    )
    parser.add_argument("-p", "--patterns", type=str, help="Optional parameter: patterns to be searched (comma-separated string).")
    parser.add_argument("--path", type=str, help="Relative path, starting from the knowledge base root, to a subdirectory.")
    parser.add_argument("-a", "--activity", type=str, help="Limit the search to a specific activity.")
    parser.add_argument("-g", action="store_true", help="Glossary. Prioritize the search in the glossary")
    parser.add_argument("-l", action="store_true", help="Large context (increases context size limit from 200k to 500k)")
    parser.add_argument("-org", action="store_true", help="Prioritise team Organisation matches")
    parser.add_argument("-r", action="store_true", help="Recursively run the search on the previous context (i.e. to reduce the size)")
    parser.add_argument("-v", action="store_true", help="Verbose console output")
    parser.add_argument("-vv", action="store_true", help="Very Verbose console output")
    parser.add_argument("-kb0", action="store_true", help="Use kb0 knowledge base 'MotionWise Classic Communication' (default)")
    parser.add_argument("-kb2", action="store_true", help="Use kb2 knowledge base 'Automotive Papers and Presentations (from Salva)'")
    parser.add_argument("-days", type=int, default=None, metavar="N", help="Search only in activities modified in the last N days (default: search all)")
    parser.add_argument("-nr", action="store_true", help="Non-recursive: search only in the top-level of each activity directory (default: recursive)")
    parser.add_argument("question", type=str, help="Mandatory parameter: the question or pattern to be searched.")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-sfc", action="store_true", help="Skip pattern search in File Content")
    group.add_argument("-sfn", action="store_true", help="Skip pattern search in File Names")

    try:
        args = parser.parse_args(cmd_line_args)
    except SystemExit:
        return None
    return args


def main(cmd_line_args):
    sys.excepthook = excepthook

    args = parse_arguments(cmd_line_args)
    if args is None:
        return

    # Determine which knowledge base to use
    if args.kb2:
        kb_name = 'kb2'
    else:
        kb_name = 'kb0'  # Default to kb0
    
    CONFIG = load_config(kb_name)
    if CONFIG is None:
        return None

    # Copy the value of 'question' to the clipboard
    question = args.question
    pyperclip.copy(question) 
    
    try_glossary = False
    patterns = args.patterns
    if not patterns:
        print(f"ERROR: [dynamic_context.py] Pattern is required. To be fixed in the future. For now, please use -p to specify the pattern.")
        return None
    if question and not patterns:
        patterns = get_patterns(question, CONFIG)
        return None
    elif question and patterns:
        patterns = patterns.split(",")
    else:
        print(f"ERROR: [dynamic_context.py] Wrong parameters.")
        return None
    assert type(patterns) is list, "patterns must be a list"
    
    # Define the output file path
    output_file = os.path.join(TEMPORARY_DIR, 'dynamic_context', 'dynamic_context.1bf.md')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Get the relevant directories
    base_dir = os.path.dirname(__file__)
    files = []
    doc_props = None
    
    if args.r:
        files = [output_file, ]
    else:
        if 'activities' not in CONFIG['kb_config']:
            print(f"ERROR: cannot find 'activities' entry in configuration")
        
        search_dir = CONFIG['kb_config']['activities']
        if args.path:
            kb_path = CONFIG['kb_path']
            search_dir = os.path.join(kb_path, args.path)
        if args.activity:
            search_dir = os.path.join(search_dir, args.activity)
        if args.days is not None:
            cutoff_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%d')
            activity_dirs = sorted([
                os.path.join(search_dir, d)
                for d in os.listdir(search_dir)
                if os.path.isdir(os.path.join(search_dir, d))
            ])
            filtered_dirs = [
                p for p in activity_dirs
                if (get_activity_date(p) or '') >= cutoff_date
            ]
            print(f"Filtering to {len(filtered_dirs)} activities modified in the last {args.days} days")
            for activity_path in filtered_dirs:
                if args.nr:
                    files.extend(glob.glob(os.path.join(activity_path, '*.md')))
                else:
                    files.extend(glob.glob(os.path.join(activity_path, '**', '*.md'), recursive=True))
        else:
            if args.nr:
                files.extend(glob.glob(os.path.join(search_dir, '*', '*.md')))
            else:
                files.extend(glob.glob(os.path.join(search_dir, '**', '*.md'), recursive=True))

        # if 'manual_comments_dir' in CONFIG['kb_config']:
        #     dir = CONFIG['kb_config']['manual_comments_dir']
        #     files.extend(glob.glob(os.path.join(dir, '**', '*.txt'), recursive=True))
        #     files.extend(glob.glob(os.path.join(dir, '**', '*.md'), recursive=True))
        # 
        # if 'my_comments_dir' in CONFIG['kb_config']:
        #     dir = CONFIG['kb_config']['my_comments_dir']
        #     files.extend(glob.glob(os.path.join(dir, '**', '*.txt'), recursive=True))
        #     files.extend(glob.glob(os.path.join(dir, '**', '*.md'), recursive=True)) 
        # 
        # if 'imports_dir' in CONFIG['kb_config']:
        #     dir = CONFIG['kb_config']['imports_dir']
        #     files.extend(glob.glob(os.path.join(dir, '**', '*.txt'), recursive=True))
        #     files.extend(glob.glob(os.path.join(dir, '**', '*.md'), recursive=True))
        # 
        # if 'pdf_import_dir' in CONFIG['kb_config']:
        #     dir = CONFIG['kb_config']['pdf_import_dir']
        #     files.extend(glob.glob(os.path.join(dir, '**', '*.txt'), recursive=True))
        #     files.extend(glob.glob(os.path.join(dir, '**', '*.md'), recursive=True))
        # 
        # if args.g or try_glossary:
        #     import pdb; pdb.set_trace()
        #     # Move files containing "glossary" to the beginning of the list
        #     glossary_files_list = [f for f in files if "\\glossary\\" in f.lower()]
        #     other_files_list = [f for f in files if "\\glossary\\" not in f.lower()]
        #     files = organisation_files_list + other_files_list
        # 
        # if args.org:
        #     # Move files containing "organisation" to the beginning of the list
        #     organisation_files_list = [f for f in files if "\\organisation\\" in f.lower()]
        #     other_files_list = [f for f in files if "\\organisation\\" not in f.lower()]
        #     files = organisation_files_list + other_files_list

        files = [f for f in files if "readme." not in f.lower()]
    
        doc_props = doc_properties(files)
        

    print(f"Searching in {len(files)} files")
    
    # Compile the pattern as a regex
    print(f"Contextualizing for: '{patterns}'")
    regex_list = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]

    # Min and Max size of the created context file
    context_max_size = 500_000 if args.l else 200_000
    
    # Context collected by matching file name.
    out_content_1 = collect_context_by_filename(files, regex_list, doc_props, args)

    # Context collected by searching in the content
    out_content_2 = collect_context_by_content(files, regex_list, len(out_content_1), context_max_size, doc_props, args)
    if out_content_2 is None:
        return None

    encoded = (out_content_1 + out_content_2).encode('utf-8')
    
    if len(encoded) > context_max_size:
        encoded = reduce_context_size(encoded, context_max_size, regex_list, args)

    if len(encoded)==0:
        print(f"ERROR: cannot find any pattern match in the text-base")
        return None
    if len(encoded) > context_max_size:
        print(f"WARNING: The context size is too large. It has been truncated from {len(encoded) / 1024:.1f} kB to {int(context_max_size / 1000)} kB")
        encoded = encoded[:context_max_size]    # Truncate the output file
    
    # Write the output to a file
    decoded = encoded.decode('utf-8', errors='ignore')
    with open(output_file, 'w', encoding='utf-8', errors='replace') as f:
        f.write(decoded)
    if args.v or args.vv:
        file_size = os.path.getsize(output_file)
        print(f"Created '{output_file}' ({len(decoded.splitlines())} lines, {file_size} bytes)")

    # Clean and Compress
    sys.argv = ['clean_1bf.py', output_file]
    clean_1bf.main()
    sys.argv = ['compress_1bf.py', output_file]
    compress_1bf.main()
    sys.argv = ['clean_1bf.py', output_file]
    clean_1bf.main()

    file_size = os.path.getsize(output_file)
    if args.v or args.vv:
        file_size = os.path.getsize(output_file)
        print(f"Size after removing duplicates {file_size / 1024:.1f} kB")

    if not args.v and not args.vv:
        file_size = os.path.getsize(output_file)
        print(f"Created '{os.path.basename(output_file)}' ({len(decoded.splitlines())} lines, {file_size / 1024:.1f} kB)\n")

    results = [{"title": "dynamic_context", "type": "1bf", "path": output_file, "size": os.path.getsize(output_file)}]
    return results

if __name__ == "__main__":
    main(sys.argv[1:])

# import pdb; pdb.set_trace()
