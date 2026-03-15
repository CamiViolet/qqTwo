# Script: dynamic_context.py
# Description: Create a dynamic context (1bf - One Big File).
# Usage: python dynamic_context.py pattern
#
# Parameters:
#   pattern - String to be searched (regex)
#
# Examples:
#   python dynamic_context.py "smoke tests" -p "smoke.?tests" 

import argparse
import json
import os
import glob
import pyperclip
import re
import sys
from collections import defaultdict
from patterns import get_patterns
from dotenv import load_dotenv
import tempfile


common_words_to_ignore = ['shall', 'none', 'document', 'documentation', 'describe', 'described', 'describes']

config = None

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
                        cumulative_out_content = cumulative_out_content + f"\nFile (by content): {file_name}\n\n" + windows_content
                        files_count += 1
                        if args.vv:
                            print(f"By content: file:{file} occurrences:{occurrences} original_size:{original_size} extracted_context_size:{len(windows_content)} density:{density} occurrences/MB")
        if args.v or args.vv:
            print(f"By content (iteration {iteration}): window_radius:{window_radius} files_count:{files_count} context_size:{len(cumulative_out_content) / 1024:.1f} kB")
        context_size = len_out_content_1 + len(cumulative_out_content)
        if context_size > 10*context_max_size:
            print(f"ERROR: too many matches. Please refine the search patterns.")
            sys.exit(1)
            
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
    if args.sfn:
        return ""

    if not args.patterns:
        # Load the words.json file
        keywords_file = os.path.join(os.path.dirname(__file__), "..", "kb0", "words.json")
        with open(keywords_file, 'r', encoding='utf-8') as f:
            keywords = json.load(f)     # Such words are lower case and singular
        keywords_max_freq = next(iter(keywords.items()))[1]

        # Load the ngrams.json file
        ngrams_file = os.path.join(os.path.dirname(__file__), "..", "kb0", "ngrams.json")
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
                cumulative_out_content = f"\nFile (by name): {file_name}\n\n{file_type_str}" \
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


def load_json(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


def parse_arguments():
    parser = argparse.ArgumentParser(description="Create a dynamic context by using the input parameter.")
    parser.add_argument("-p", "--patterns", type=str, help="Optional parameter: patterns to be searched (comma-separated string).")
    parser.add_argument("-g", action="store_true", help="Glossary. Prioritize the search in the glossary")
    parser.add_argument("-l", action="store_true", help="Large context (increases context size limit from 200k to 500k)")
    parser.add_argument("-org", action="store_true", help="Prioritise team Organisation matches")
    parser.add_argument("-v", action="store_true", help="Verbose console output")
    parser.add_argument("-vv", action="store_true", help="Very Verbose console output")
    parser.add_argument("question", type=str, help="Mandatory parameter: the question or pattern to be searched.")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-sfc", action="store_true", help="Skip pattern search in File Content")
    group.add_argument("-sfn", action="store_true", help="Skip pattern search in File Names")

    return parser.parse_args()


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


def context(args, patterns):
    global config
    if not config:
        config = load_json(config_file = os.path.join(os.path.dirname(__file__), "config.json"))

    # Define the output file path
    tmp_dir = tempfile.gettempdir()
    output_file = os.path.join(tmp_dir, 'dynamic_context', 'dynamic_context.1bf.txt')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Collect the text files
    knowledge_base = config['knowledge_base']
    files = glob.glob(os.path.join(knowledge_base, '**/*.txt'), recursive=True)
    files += glob.glob(os.path.join(knowledge_base, '**/*.md'), recursive=True)
    files = [f for f in files if "readme." not in f.lower()]
    files = [f for f in files if '.1bf.txt' not in f.lower()]
    import pdb; pdb.set_trace()
    
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

    encoded = (out_content_1 + out_content_2).encode('utf-8')
    
    if len(encoded) > context_max_size:
        encoded = reduce_context_size(encoded, context_max_size, regex_list, args)

    error_code = 0
    if len(encoded)==0:
        print(f"ERROR: cannot find any pattern match in the text-base")
        error_code = 1
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
    
    return error_code


if __name__ == "__main__":

    sys.excepthook = excepthook
    
    error_code = 0

    args = parse_arguments()

    # load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

    # Copy the value of 'question' to the clipboard
    question = args.question
    pyperclip.copy(question) 
    
    patterns = args.patterns
    if question and not patterns:
        patterns = get_patterns(question)
        sys.exit(1)
    elif question and patterns:
        patterns = patterns.split(",")
    else:
        print(f"ERROR: [dynamic_context.py] Wrong parameters.")
        sys.exit(1)
    assert type(patterns) is list, "patterns must be a list"
    
    error_code = context(args, patterns)
    
    sys.exit(error_code)
# import pdb; pdb.set_trace()
