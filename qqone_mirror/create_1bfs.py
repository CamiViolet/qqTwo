'''
usage: create_1bfs.py [-h] [-v] [-vv] [activity_name]

Generate the 1bf (One Big File) for all the activities

positional arguments:
  activity_name  Generate the 1bf only for the specified topic (default: all activities)

options:
  -h, --help  show this help message and exit
  -v          Verbose console output
  -vv         Very Verbose console output

Example:
    python create_1bfs.py --network sprtorcas_1613_security_concept_for_dds_com_tlc
  '''

import argparse
from getpass import getpass
import json
import glob
import os
import re
import sys
from collections import defaultdict
from library import load_json, doc_properties, load_config, excepthook
from web_to_markdown import fetch_web_page, fetch_confluence_page
from dotenv import load_dotenv
import yaml

global config, password

password = None


def collect_context_by_content(files, regex_list, doc_props, context_window_size, args):
    """
    Collect context by searching for regex matches within file contents, using a window mechanism.
    Returns out_content
    """

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
                windows_content, occurrences = extract_context_windows(content, regex_list, context_window_size)
                original_size = os.path.getsize(file)
                density = int(1_000_000 * occurrences / original_size) if original_size else 0
                if occurrences:
                    cumulative_out_content = cumulative_out_content + f"\nFile: (by content) {file_name}\n\n" + windows_content
                    files_count += 1
                    if args.vv:
                        print(f"By content: file:{file} occurrences:{occurrences} original_size:{original_size} extracted_context_size:{len(windows_content)} density:{density} occurrences/MB")

    return cumulative_out_content


def collect_context_by_filename(files, regex_list, doc_props, args):
    """
    Collect context by matching file names against regex_list.
    Returns (out_content)
    """

    cumulative_out_content = ""  # Selected content by file name
    selected_files = []
    files_count = 0
    for file in files:
        file_name = os.path.basename(file)
        file_name_matching = any(regex.search(file_name) for regex in regex_list)
        if file_name_matching:  # Check if the file name matches any regex
            # If the file name matches the regex, then get the full content of the file
            selected_files.append(file)
            if args.v:
                print(f"Matching file name: {file_name}")
            if args.vv:
                print(f"Matching file path: {file}")
            with open(file, 'r', encoding='utf-8', errors='replace') as f:
                files_count += 1
                file_type = doc_props.get(file, {}).get('file_type')
                file_type_str = ""
                if file_type:
                    file_type_str = f"File Type: {file_type}\n\n"
                cumulative_out_content += f"\nFile: (by name) {file_name}\n\n{file_type_str}" \
                    + f.read()
    if args.v or args.vv:
        print(f"By file name: files_count:{files_count} context_size:{len(cumulative_out_content) / 1024:.1f} kB")
    return (cumulative_out_content, selected_files)


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
    
    
def format_polarion_work_item(id, pol_items):

    item = pol_items[id]

    type = item['Type']
    requirement_type = item['Requirement Type']
    title = item['Title']
    description = item['Description']
    safety_level = item['Safety Level'] # if 'Safety Level' in item else None
    safety_relevant = item['Safety Relevant'] # if 'Safety Relevant' in item else None
    cybersecurity_level = item['Cybersecurity Level'] # if 'Cybersecurity Level' in item else None
    security_relevant = item['Cybersecurity Level'] # if 'Cybersecurity Level' in item else None
    verification_criteria = item['Verification Criteria']
    verification_method = item['Verification Method']
    linked_work_items = item['Linked Work Items'] # if 'Linked Work Items' in item else None
    assumed_requirement = item['Ard'] if 'Ard' in item else None
    include_in = item['Include In']
    swe1requirement = item['Swe1requirement']
    windchill_id = item['Windchill Id'] if 'Windchill Id' in item else None
    test_specification = item['Test Specification'] if 'Test Specification' in item else None
    assignees = item["Assignee(s)"] if "Assignee(s)" in item else None
    status = item["Status"] if "Status" in item else None
    verification_completeness_comment = item["Verification Completeness Comment"] if "Verification Completeness Comment" in item else None
    comments = item["Comments"] if "Comments" in item else None

    verification_criteria_formatted = verification_criteria
    if "\n" in verification_criteria:
        verification_criteria_formatted = "\n        " + verification_criteria.replace("\n", "\n        ")

    verification_completeness_comment_formatted = verification_completeness_comment
    if verification_completeness_comment and "\n" in verification_completeness_comment:
        verification_completeness_comment_formatted = "\n        " + verification_completeness_comment.replace("\n", "\n        ")

    linked_work_items_formatted = linked_work_items.replace('\n', '\n        ')
        
    # Change to boolean
    assumed_requirement_bool = (assumed_requirement.lower()=='yes') if assumed_requirement else None
    swe1requirement_bool = (swe1requirement.lower()=='yes')

    text = []
    text.append("\nid=%s" % (id))
    text.append("    type=%s" % (type))
    if requirement_type:
        text.append("    requirement_type=%s" % (requirement_type))
    if title:
        text.append("    title=%s" % (title))
    if description:
        text.append("    description=%s" % (description))
    if safety_level:
        text.append("    safety_level=%s" % (safety_level))
    if safety_relevant:
        text.append("    safety_relevant=%s" % (safety_relevant))
    if cybersecurity_level:
        text.append("    cybersecurity_level=%s" % (cybersecurity_level))
    if security_relevant:
        text.append("    security_relevant=%s" % (security_relevant))
    if verification_method:
        text.append("    verification_method=%s" % (verification_method))
    if verification_criteria_formatted:
        text.append("    verification_criteria=%s" % (verification_criteria_formatted))
    if linked_work_items_formatted:
        text.append("    linked_work_items=%s" % (linked_work_items_formatted))
    if assumed_requirement:
        text.append("    assumed_requirement=%s" % (assumed_requirement))
    if include_in:
        text.append("    include_in=%s" % (include_in))
    if swe1requirement:
        text.append("    swe1requirement=%s" % (swe1requirement))
    if windchill_id:
        text.append("    windchill_id=%s" % (windchill_id))
    if test_specification:
        text.append("    test_specification=%s" % (test_specification))
    if assignees:
        text.append("    assignees=%s" % (assignees))
    if status:
        text.append("    status=%s" % (status))
    if verification_completeness_comment_formatted:
        text.append("    verification_completeness_comment=%s" % (verification_completeness_comment))
    if comments:
        text.append("    comments=%s" % (comments))   

    return(text)
    
    
def get_manual_notes(manual_notes_file, tag_pattern):
    # Process the file to collect tagged sections
    
    try:
        tag_regex = re.compile(tag_pattern, re.IGNORECASE)
    except re.error as e:
        print(f"ERROR: Invalid regex pattern in 'context_window_patterns': {e}.")
        print(f"Patterns: {tag_pattern}")
        sys.exit(1)
    
    out_content = ""
    
    # Read the source file and find lines containing the tag
    with open(manual_notes_file, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # If the line matches the tag regex
        found = tag_regex.search(line)
        if "personal_opinions" in line.lower() \
            and tag_pattern!="#tag_personal_opinions_text_base":
            # Take tag_personal_opinions_text_base only if explicitly requested
            found = False
        if found:
            # Determine the indentation level of the tagged line
            tagged_line_indent = len(line) - len(line.lstrip())
            
            # Start a new section with the tagged line
            current_section = [line]
            i += 1
            
            # Collect all subsequent lines with greater indentation
            while i < len(lines):
                next_line = lines[i]
                next_line_indent = len(next_line) - len(next_line.lstrip())
                
                # If the next line has greater indentation than the tagged line or is empty, add it
                if next_line.strip() == "" or next_line_indent > tagged_line_indent:
                    current_section.append(next_line)
                    i += 1
                else:
                    # Stop collecting when we hit a line with same or less indentation
                    break
            
            # Add the collected section to our results
            out_content += '\n' + ''.join(current_section)
        else:
            i += 1

    return(out_content)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate the 1bf (One Big File) for all the activities")
    parser.add_argument("activity_name", nargs="?", default=None, help="Generate the 1bf only for the specified topic (default: all activities)")
    parser.add_argument("-v", action="store_true", help="Verbose console output")
    parser.add_argument("-vv", action="store_true", help="Very Verbose console output")
    parser.add_argument("--network", action="store_true", help="Allows fetching web pages (disabled by default for performance reasons)")

    return parser.parse_args()


def run_command(command_data, args):
    # Run the command and append the output to out_content
    global config, password
    
    kb_path = config['kb_config']['kb_path']

    command = command_data.get('command')

    base_dir = os.path.dirname(__file__)

    out_content = ""

    if command=="get_files":
        # Command 'get multiple files file with context-window'
        
        search_path = command_data.get('search_path')   # Mandatory parameter
        file_search_patterns = command_data.get('file_search_patterns', ['.*'])     # Default: all files
        recurse_subdirs = command_data.get('recurse_subdirs', True)     # Default: recurse subdirectories
        context_window_patterns = command_data.get('context_window_patterns', [])   # Default: no context window
        context_window_size = command_data.get('context_window_size', 50)   # Default: 50
    
        try:
            file_pattern_list = [re.compile(pattern, re.IGNORECASE) for pattern in file_search_patterns]
        except re.error as e:
            print(f"ERROR: Invalid regex pattern in 'file_search_patterns': {e}.")
            print(f"Patterns: {file_search_patterns}")
            sys.exit(1)

        if not os.path.isabs(search_path):
            search_path = os.path.join(kb_path, search_path)
    
        matching_files = []
        
        if os.path.isfile(search_path):
            matching_files.append(search_path)
        elif os.path.isdir(search_path):
            for root, dirs, files in os.walk(search_path):
                if not recurse_subdirs:
                    dirs.clear()
                for file in files:
                    file_path = os.path.join(root, file)
                    if any(pattern.search(file_path) for pattern in file_pattern_list):
                        matching_files.append(file_path)
        
        matching_files = [f for f in matching_files if f.endswith('.txt') or f.endswith('.md')]
    
        if not matching_files:
            print(f"ERROR: No files found matching the patterns '{file_search_patterns}' in '{search_path}'")
    
        try:
            regex_list = [re.compile(pattern, re.IGNORECASE) for pattern in context_window_patterns]
        except re.error as e:
            print(f"ERROR: Invalid regex pattern in 'context_window_patterns': {e}.")
            print(f"Patterns: {context_window_patterns}")
            sys.exit(1)
        
        for file in matching_files:
            with open(file, 'r', encoding='utf-8', errors='replace') as f:
                file_content = f.read()
    
            if regex_list:
                (context_windows, _) = extract_context_windows(file_content.split('\n'), regex_list, context_window_size)
            else:
                context_windows  = file_content
            if context_windows.strip():
                out_content += "\n\nFile: " + file + "\n\n"
                out_content += context_windows        


    elif command=="get_manual_notes":

        # Command 'get_manual_notes': Search in 'manual notes' by tag
        
        # TODO: change the name to 'get_log'
        
        search_tag = command_data.get('search_tag')   # Mandatory parameter
        context_window_patterns = command_data.get('context_window_patterns', [])   # Default: no context window
        context_window_size = command_data.get('context_window_size', 50)   # Default: 50
        
        content = get_manual_notes(r"C:\Dev_TTT\dox\log.txt", search_tag)

        try:
            regex_list = [re.compile(pattern, re.IGNORECASE) for pattern in context_window_patterns]
        except re.error as e:
            print(f"ERROR: Invalid regex pattern in 'context_window_patterns': {e}.")
            print(f"Patterns: {context_window_patterns}")
            sys.exit(1)

        if regex_list:
            (context_windows, _) = extract_context_windows(content.split('\n'), regex_list, context_window_size)
        else:
            context_windows = content

        description = f'Manual Notes'
        out_content += f"\n\nFile: {description}\n\n"
        out_content += context_windows


    elif command=="get_polarion_items":

        work_item_ids = command_data.get('work_item_ids')
        
        pol_items_path = config['kb_config']['all_polarion_items']

        pol_items = load_json(pol_items_path)
        
        formatted_item = []
        for id in work_item_ids.split(','):
            if id in pol_items:
                formatted_item += format_polarion_work_item(id, pol_items)
        
        out_content += '\n'.join(formatted_item)


    elif command=="get_url_page":

        # Command 'get_url_page': Get a web page content

        if not args.network:
            return(None)

        url = command_data.get('url')

        out_content += f"\n\nUrl: {url}\n"

        out_content +=  fetch_web_page(url)

        import pdb; pdb.set_trace()


    elif command=="get_confluence_page":

        # Command 'get_confluence_page': Get a Confluence page content

        if not args.network:
            return(None)

        url = command_data.get('url')

        if not password:
            password = getpass("Enter the password: ")

        out_content +=  "<!-- SPLIT THE FILE -->"
        out_content +=  fetch_confluence_page(url, os.environ.get('USER', ''), password)
        
        print(f"Fetched {url}")


    elif command=="search_knowledge_base":
    
        ''' 
        Command 'search_knowledge_base': Search in knowledge-base by 'patterns'
        
        Search in the full knowledge-base by using the given regexes.
        Parameters:
        context_window_patterns : list of regexes. Searches are case-insentive.
        context_window_size : size of the context window to be used in case of match.
        '''
    
        context_window_patterns = command_data.get('context_window_patterns')   # Mandatory parameter
        context_window_size = command_data.get('context_window_size', 50)   # Default: 50
        
        try:
            regex_list = [re.compile(pattern, re.IGNORECASE) for pattern in context_window_patterns]
        except re.error as e:
            print(f"ERROR: Invalid regex pattern in 'context_window_patterns': {e}.")
            print(f"Patterns: {context_window_patterns}")
            sys.exit(1)

        files = glob.glob(os.path.join(kb_path, 'imports', '**', '*.txt'), recursive=True)
        files += glob.glob(os.path.join(kb_path, 'imports', '**', '*.md'), recursive=True)

        files = [f for f in files if "readme." not in f.lower()]
        
        doc_props = doc_properties(files)

        (cumulative_out_content, selected_files) = collect_context_by_filename(files, regex_list, doc_props, args)
        out_content += cumulative_out_content
        
        remaining_files = [f for f in files if f not in selected_files]

        out_content += collect_context_by_content(remaining_files, regex_list, doc_props, context_window_size, args)

        
    else:
        print(f"ERROR: Unknown command '{command}' in configuration.")

    return(out_content)


def run_script(config_file, activity_dir, activity_name, args):
    # Run the script for the current topic

    with open(config_file, 'r', encoding='utf-8') as f:
        local_config = yaml.safe_load(f)
    if not local_config:
        return    # TODO: this happens for activities with the old style. To be removed in the future.
    if type(local_config) is not dict:
        return
    if "commands" not in local_config:
        return

    if 'output_file_name' in local_config:
        output_file_name = local_config['output_file_name']
    else:
        output_file_name = activity_name
    generated_file_dir = os.path.join(activity_dir, "raw")
    if not os.path.exists(generated_file_dir):
        os.makedirs(generated_file_dir)
    output_file_path = os.path.join(generated_file_dir, output_file_name + ".gitignore.1bf.txt")

    already_exists = os.path.exists(output_file_path)
    # if already_exists:
    #    os.remove(output_file_path)

    out_content = ""
    description = local_config.get('description')
    if description:
        out_content += f"Description: {description}\n\n"
    updated = local_config.get('updated')
    if updated:
        out_content += f"\n\nUpdated: {updated}\n\n"

    # Run the commands
    for command_data in local_config.get('commands', []):
        content = run_command(command_data, args)  # Run the command and append the output to out_content
        if content is None:
            return  # The script is requesting to skip the generation of the 1bf (e.g. when trying to fetch a web page without --network option).
        out_content += content
        
    # String replace
    for replace in local_config.get('replaces', []):
        out_content = re.sub(replace[0], replace[1], out_content)

    out_contents = out_content.split('<!-- SPLIT THE FILE -->')
    for i, content in enumerate(out_contents):
        if len(out_contents)>1:
            file_path = output_file_path.replace('.1bf.txt', f'.part{i+1}.1bf.txt')
        else:
            file_path = output_file_path
        encoded = content.encode('utf-8')
        decoded = encoded.decode('utf-8', errors='ignore')
        with open(file_path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(decoded)
        if args.v or args.vv:
            file_size = os.path.getsize(file_path)
            print(f"Created/updated '{file_path}' ({len(decoded.splitlines())} lines, {file_size} bytes)")
        else:
            if already_exists:
                print(f"Updated '{file_path}'")
            else:
                print(f"Created '{file_path}'")
    return


def main():
    global config
    
    sys.excepthook = excepthook

    args = parse_arguments()

    load_dotenv()

    config = load_config('kb0')

    kb_path = config['kb_config']['kb_path']

    config_files = glob.glob(os.path.join(kb_path, "**", "1bf_config*.yaml"), recursive=True)
    
    found = False
    for config_file in config_files:
        if '.gitignore' in config_file:
            continue

        # Process only activities given as argument
        activity_dir = os.path.dirname(os.path.dirname(config_file))
        activity_name = os.path.basename(activity_dir)
        if args.activity_name and args.activity_name.lower()!=activity_name.lower():
            continue

        run_script(config_file, activity_dir, activity_name, args)     # Run the script for the current topic
        
        found = True
        
    if not found:
        print("Error: cannot find any '1bf_config*.yaml' file")

    # Create the file config_example.gitignore.json with the content of all the config files.
    config_example_json = ""
    for config_file in config_files:
        with open(config_file, 'r', encoding='utf-8', errors='replace') as f:
            config_example_json += f.read() + "\n"

    example_config_json_path = os.path.join(kb_path, "config_example.gitignore.yaml")
    with open(example_config_json_path, 'w', encoding='utf-8', errors='replace') as f:
        f.write(config_example_json)
    if args.v or args.vv:
        print(f"Created example file with the content of all the config files: {example_config_json_path}")    

    return


if __name__ == "__main__":
    main()

# import pdb; pdb.set_trace()
