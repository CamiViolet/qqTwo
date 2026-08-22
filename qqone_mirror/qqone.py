# Script: qqOne.py

import find_activities
import new_activity
import dynamic_context
from datetime import datetime
import glob
import html2text
import json
import os
import pyperclip
import re
import shlex
import shutil
import subprocess
import sys
import webbrowser
import win32clipboard
import win32con
import xml.etree.ElementTree as ET
import readline     # pip install pyreadline3
from dotenv import load_dotenv
from library import get_activity_size, get_doc_properties, get_doc_properties2, normalize_to_C_symbol, print_results_to_console, normalize_to_filename, search_for_file, write_file_with_properties


file_list1 = None
prev_results = []       # List of previous search results. Each item is a pair of (text_to_display, data)
case_sensitive = re.IGNORECASE      # values 0:case-sensitive, 2:re.IGNORECASE
current_script_content = None

filter_out_from_confluence_pages = [
    "Skip to sidebar",
    "Skip to main content",
    "Skip to breadcrumbs",
    "Skip to search",
    "Linked Applications",
    "Edit View inline comments",
    "Save for later Watching Share",
    "Stop watching this issue",
    "Create branch"
]


def excepthook(type, value, tb):
    import traceback, pdb
    traceback.print_exception (type, value, tb)
    print
    pdb.pm ()


class MyCompleter(object):

    def __init__(self, options):
        self.options = sorted(options)

    def complete(self, text, state):
        if state == 0:  # on first trigger, build possible matches
            if text:  # cache matches (entries that start with entered text)
                self.matches = [s for s in self.options
                                    if s and s.startswith(text)]
            else:  # no text entered, all matches possible
                self.matches = self.options[:]

        # return match indexed by state
        try:
            return self.matches[state]
        except IndexError:
            return None


def clean_text(text):
    out_text = ""
    previous = None
    for i, line in enumerate(text.split('\n')):
        # Check if line contains any string from filter_out_from_confluence_pages
        if any(filter_str in line for filter_str in filter_out_from_confluence_pages):
            continue  # Skip this line

        if "dcdddInfdi" in line:    # Skip a specific lines
            continue

        line = line.rstrip() + '\n'

        if line=='\n' and previous=='\n':
            continue

        out_text += line

        previous = line

    return(out_text)


def clear_console():
    # For Windows
    if os.name == 'nt':
        os.system('cls')
    # For Unix/Linux/MacOS
    else:
        os.system('clear')


def create_valid_filename(page_title, jira_issue_id = None):
    file_name = page_title

    file_name = file_name.encode('ascii', 'ignore').decode('ascii')
    file_name = re.sub(r'[^a-zA-Z0-9]', '_', file_name)

    if jira_issue_id:
        file_name = jira_issue_id + '_' + file_name

    file_name = re.sub(r'_+', '_', file_name)

    return(file_name)


def extract_data_from_confluence_page(page_url, page_text, option_cb, option_org):
    lines = page_text.split('\n')

    lines = [line.strip() for line in lines]

    page_type = None
    page_title = None

    if "https://confluence.tttech.com" in page_url:
        page_type = "Confluence"

        if option_cb:
            page_type += "/Cookbook"

        if option_org:
            page_type += "/Organization"

        for i, line in enumerate(lines):
            if "Analytics" in line and (i + 2 < len(lines)) and lines[i + 2].startswith("Created by"):
                page_title = lines[i + 1].strip()
                break

    if "https://issues.tttech.com" in page_url:
        page_type = "Jira"

        issue = page_url.split('/')[-1]

        for i, line in enumerate(lines):
            if issue in line and (i + 1 < len(lines)):
                page_title = lines[i + 1].strip()
                break

    if "https://polarion.tttech-auto.com" in page_url:
        page_type = "Polarion"
        page_title = '_'.join(page_url.split('/')[-2:])
        page_title = page_title.replace('%20', ' ').replace('__', '_').replace('_', ' ')



    return(page_type, page_title)


def merge_keywords(export_path, page_text):
    """
    Reads the first lines of export_path and collects lines that start with 'keywords:'.
    Returns page_text with those keyword lines added on top.
    """
    keyword_lines = []
    with open(export_path, 'r', encoding='utf-8') as fl:
        for i in range(10):
            line = fl.readline()
            if not line:
                break
            line_stripped = line.strip(' \n\t-')
            if re.match(r'^keywords\s*:', line_stripped, re.IGNORECASE):
                line_stripped = re.sub(r'keywords\s*:', 'Keywords:', line_stripped, flags=re.IGNORECASE)
                keyword_lines.append(line_stripped)

    if keyword_lines:
        keywords_text = '\n' + '\n'.join(keyword_lines) + '\n'
        return keywords_text + page_text

    return page_text


def get_param_from_cli(option, cmd_list, new_cmd_list=None):
    """
    This helper is used to detect and extract single-token options (e.g. '-x', '-l', '-cr')
    from a command argument list while optionally collecting them into a separate list ('new_cmd_list').
    Such optional list can be used to forward the parameters to a further command.
    """
    if option:
        if option in cmd_list:
            cmd_list.remove(option)
            if new_cmd_list is not None:
                new_cmd_list.append(option)
            return True
        return False
    else:   # Search for a positional parameter
        if len(cmd_list)>=2 and (not cmd_list[1].startswith('-')):
            param = cmd_list[1]
            cmd_list.remove(param)
            return(param)
        return None


def get_text_bases_path(text_bases):
    # Translates text_bases names to a path
    text_base_paths = []
    for path in text_bases:
        base_dir = r"C:\dev0\kb0"
        path = os.path.join(base_dir, path)
        assert os.path.isfile(path), f"Path is not a file: {path}"
        text_base_paths.append(path)
    return(text_base_paths)


def format_size(size_bytes):
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.2f} kB"
    else:
        return f"{size_bytes} bytes"


def open_in_vs_code(path=None, max_size=200_000):

    # Truncate the file if it exceeds max_size
    # file_size = os.path.getsize(DYNAMIC_CONTEXT_FILE)
    # if file_size > max_size:
    #     with open(DYNAMIC_CONTEXT_FILE, 'rb') as f:
    #         f.seek(-max_size, os.SEEK_END)
    #         data = f.read()
    #     with open(DYNAMIC_CONTEXT_FILE, 'wb') as f:
    #         f.write(data)

    if not path:
        path = DYNAMIC_CONTEXT_FILE

    subprocess.Popen(
        [r"C:\Users\nxg18988\AppData\Local\Programs\Microsoft VS Code\Code.exe", "--reuse-window", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )


def open_directory_in_vs_code(directory_path):
    subprocess.Popen(
        [r"C:\Users\nxg18988\AppData\Local\Programs\Microsoft VS Code\Code.exe", "--reuse-window", directory_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )


def get_clipboard_as_markdown():
    """Get clipboard content as Markdown (from HTML if available, otherwise plain text)"""
    try:
        win32clipboard.OpenClipboard()

        CF_HTML = win32clipboard.RegisterClipboardFormat("HTML Format")

        # Try to get HTML format first
        try:
            html_data = win32clipboard.GetClipboardData(CF_HTML)
            html_text = html_data.decode('utf-8', errors='ignore')

            # Convert HTML to Markdown
            h = html2text.HTML2Text()
            h.ignore_links = False
            h.body_width = 0  # Don't wrap lines
            markdown_text = h.handle(html_text)
            return markdown_text
        except TypeError:
            pass

        # Fallback to plain text
        text_data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
        return text_data.decode('utf-8', errors='ignore') if isinstance(text_data, bytes) else text_data

    finally:
        win32clipboard.CloseClipboard()

    return(None)


def open_notepad(file_path, line_number=None):
    cmd = [NOTEPADPP_PATH, file_path]
    if line_number is not None:
        cmd.append(f"-n{line_number}")
    subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def clean_ait_cache(ait_cache_path):
    cache_size = os.path.getsize(ait_cache_path) if os.path.exists(ait_cache_path) else 0
    if cache_size==0:
        print(f"Cache is already empty")
        return
    answer = input(f"Do you want to clean the cache? (cache size = {format_size(cache_size)})").strip().lower()
    if answer == "y":
        if os.path.exists(ait_cache_path):
            os.remove(ait_cache_path)
    return


def replace_numeric_indices_with_titles(cmd_list, prev_results):
    """
    Replace numeric indices in command parameters with their corresponding titles from prev_results.
    Returns the processed subprocess parameters, or None if an error occurs.
    """
    subprocess_params = cmd_list[1:]
    for i, param in enumerate(subprocess_params):
        if re.match("[0-9]+", param):
            index = int(param)
            if index > (len(prev_results)-1):
                print("ERROR: index out of range")
                return None
            subprocess_params[i] = prev_results[index]['title']
    return subprocess_params


def run(cmd):
    global file_list1
    global prev_results
    global case_sensitive
    global current_script_content

    if not cmd:
        return

    if (cmd.startswith("'") and cmd.count("'") >= 2) or (cmd.startswith('"') and cmd.count('"') >= 2):
        cmd = 'aid ' + cmd   # If the command starts with a quote, we assume it's implicitly an 'aid' command.

    try:
        cmd_list = shlex.split(cmd)
    except ValueError as e:
        print(f"ERROR: Failed to parse command: {e}")
        return


    if cmd_list[0]=="new_activity" or cmd_list[0]=="na":
        # new_activity, na : Create a new activity in the knowledge base   # tag_global_help
        subprocess_params = cmd_list[1:]
        prev_results = new_activity.main(subprocess_params)
        print_results_to_console(prev_results)


    elif cmd_list[0]=="aidynamic" or cmd_list[0]=="aid":
        # aidynamic, aid : (AI Dynamic) Ask questions to the knowledge base  # tag_global_help
        subprocess_params = cmd_list[1:]
        prev_results = dynamic_context.main(subprocess_params)
    

    elif cmd_list[0]=="cls":
        if len(cmd_list)>1 and (cmd_list[1]=='--help' or cmd_list[1]=='-h'):
            print("")
            print("cls : Clear the console.")     # tag_global_help
            print("")
            return
        clear_console()
        return


    elif cmd_list[0]=="console":
        if len(cmd_list)>1 and (cmd_list[1]=='--help' or cmd_list[1]=='-h'):
            print("")
            print("console : open the last command output with the editor.")     # tag_global_help
            print("")
            return
        subprocess.call([NOTEPADPP_PATH, r"C:\Temp\console.txt"])
        return      # to not print command duration


    elif cmd_list[0]=="debug" or cmd_list[0]=="dbg":
        if (len(cmd_list)==1) or (len(cmd_list)>1 and (cmd_list[1]=='--help' or cmd_list[1]=='-h')):
            print("")
            print("debug, dbg : Open files in Notepad++ for debugging.")     # tag_global_help
            print("")
            print("Options:")
            print("  --dynamic_context, -d : open the script dynamic_context.py")
            print("  --dynamic_1bf, -1bf   : open the file dynamic_context.1bf.txt")
            print("  --history             : open the history file")
            print("  --me                  : open the current script")
            print("")
            return

        if cmd_list[1]=="--dynamic" or cmd_list[1]=="-d":
            subprocess.call([NOTEPADPP_PATH, DYNAMIC_CONTEXT_PY_PATH])

        elif cmd_list[1]=="--dynamic_1bf" or cmd_list[1]=="-1bf":
            subprocess.call([NOTEPADPP_PATH, DYNAMIC_CONTEXT_FILE])

        elif cmd_list[1]=="--history":
            subprocess.call([NOTEPADPP_PATH, HISTORY_FILE_PATH])

        elif cmd_list[1]=="--me":
            subprocess.call([NOTEPADPP_PATH, __file__])

        else:
            print("ERROR: command '%s': wrong parameters" % (cmd_list[0]))
            return

        return      # to not print command duration


    elif cmd_list[0]=="find_activities" or cmd_list[0]=="f":
        # find_activities, f : Find/list activities in the knowledge base   # tag_global_help
        subprocess_params = replace_numeric_indices_with_titles(cmd_list, prev_results)
        if subprocess_params is None:
            return
        prev_results = find_activities.main(subprocess_params)
        print_results_to_console(prev_results)


    elif cmd_list[0]=="help" or cmd_list[0]=="h":
        # help, h : Print Help page
        current_script_content = [line for line in current_script_content if "# tag_global_help" in line]
        current_script_content = [line for line in current_script_content if "current_script_content" not in line]

        print("")
        print("Commands:")
        for line in current_script_content:
            if "line.replace" in line:
                continue
            line = line.strip()
            line = line.replace("# tag_global_help", "")
            line = line.replace('# ', "")
            line = line.replace('print("', "")
            line = line.replace('")', "")
            print("    " + line)
        print("")
        return
    

    elif cmd_list[0]=="import" or cmd_list[0]=="i":
        if len(cmd_list)>1 and (cmd_list[1]=='--help' or cmd_list[1]=='-h'):
            print("")
            print("import, i : import a web-page (Confluence, Jira, etc.) to the knowledge base")   # tag_global_help
            print("")
            print("Usage:")
            print("  import [--cb] [--org] [--um] [<activity>]")
            print("")
            print("Arguments:")
            print("  activity : (optional) To which activity the page must be imported.")
            print("")
            print("Options:")
            print("  --cb  : Save the page in the 'cookbook' folder")
            print("  --org : Save the page in the 'organisation' folder")
            print("  --um  : Save the page in the 'user manual' folder")
            print("")
            print("Notes:")
            print("When <activity> is used, the file is saved to the 'raw' directory of the activity.")
            print("When <activity> is not used, the file is saved to the 'imports' directory of the knowledge base.")
            print("")
            return

        option_cb   = get_param_from_cli('--cb', cmd_list)
        option_org  = get_param_from_cli('--org', cmd_list)
        option_um   = get_param_from_cli('--um', cmd_list)
        activity    = get_param_from_cli(None, cmd_list)

        if len(cmd_list)>1:     # If not all parameters has been consumed ...
            print(f"ERROR: wrong parameters. Use '{cmd_list[0]} -h' for help.")
            return

        answer = input(f"\nCopy the page content to the clipboard (Ctrl-A Ctrl-C) then press Enter (or 'q' to quit).").strip()
        if answer.lower() == 'q':
            return
        
        web_page_as_text = pyperclip.paste()   # This can be in plain text or in markdown format
        
        doc_properties = get_doc_properties(web_page_as_text)

        if 'title' not in doc_properties:
            doc_properties['title'] = input(f"\nEnter title of the page (or press Enter to skip) : ").strip()
            if not doc_properties['title']:
                return

        if 'updated' not in doc_properties:
            doc_properties['updated'] = [datetime.now().strftime("%Y-%m-%d")]

        file_name = normalize_to_filename(doc_properties['title'][0]) + '.md'

        jira_issue_id = None
        if 'source' in doc_properties and 'issues.tttech.com' in doc_properties['source'][0]:
            jira_issue_id = doc_properties['source'][0].split('/')[-1]    # Example: TAPSP-1220
        if 'url' in doc_properties and 'issues.tttech.com' in doc_properties['url'][0]:
            jira_issue_id = doc_properties['url'][0].split('/')[-1]    # Example: TAPSP-1220
        if jira_issue_id:
            doc_properties['jira'] = [jira_issue_id]

        dir_path = None
        if option_cb:
            dir_path = os.path.join(r"C:\dev0\kb0\imports\cookbook", file_name)
        if option_org:
            dir_path = os.path.join(r"C:\dev0\kb0\imports\organisation", file_name)
        if option_um:
            dir_path = os.path.join(r"C:\dev0\kb0\imports\user_manual", file_name)
        if jira_issue_id:
            dir_path = os.path.join(r"C:\dev0\kb0\imports\jira", file_name)
        if activity:
            activity_path = os.path.join(r"C:\dev0\kb0\activities", activity)
            if not os.path.isdir(activity_path):
                print(f"ERROR: cannot find activity '{activity}' in 'C:\\dev0\\kb0\\activities'")
                return
            raw_path = os.path.join(activity_path, 'raw')
            os.makedirs(raw_path, exist_ok=True)
            dir_path = os.path.join(raw_path, file_name)
                
        if not dir_path:
            dir_path = os.path.join(r"C:\dev0\kb0\imports\confluence", file_name)  # Default path

        if activity:
            existing_path = dir_path if os.path.isfile(dir_path) else None
        else:
            existing_path = search_for_file(r"C:\dev0\kb0\imports", file_name)
            if existing_path and (dir_path!=existing_path):
                print(f"ERROR: file already exist in a different path: '{existing_path}'")
                return
        if existing_path:
            doc_properties_existing = get_doc_properties2(existing_path)
            for key, value in doc_properties_existing.items():  # Merge properties from doc_properties_existing to doc_properties if they are not present in doc_properties
                if key not in doc_properties:
                    doc_properties[key] = value
        
        write_file_with_properties(dir_path, doc_properties, web_page_as_text)
        
        prev_results = [{"title": doc_properties['title'], "type": "kb", "path": dir_path, "size": get_activity_size(dir_path)}, ]

        if existing_path:
            print(f"Updated file {dir_path}\n")
        else:
            print(f"Created file {dir_path}\n")

        return


    elif cmd_list[0]=="jira" or cmd_list[0]=="j":
        # jira, j : Elaborate Jira issues into a readable markdown summary.   # tag_global_help
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jira_elaborate.py")
        subprocess_params = replace_numeric_indices_with_titles(cmd_list, prev_results)
        if subprocess_params is None:
            return
        try:
            subprocess.run([r"python", script_path] + subprocess_params, check=True)
        except subprocess.CalledProcessError as e:
            pass


    elif cmd_list[0]=="mermaid_to_images" or cmd_list[0]=="merma":
        # mermaid_to_images, merma : Convert Mermaid diagrams to PNG files.   # tag_global_help
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mermaid_to_images.py")
        subprocess_params = replace_numeric_indices_with_titles(cmd_list, prev_results)
        if subprocess_params is None:
            return
        try:
            subprocess.run([r"python", script_path] + subprocess_params, check=True)
        except subprocess.CalledProcessError as e:
            pass


    elif cmd_list[0]=="manual_notes" or cmd_list[0]=="manu":
        # manual_notes, manu : Extract notes from the log file matching a pattern.   # tag_global_help
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manual_notes.py")
        subprocess_params = replace_numeric_indices_with_titles(cmd_list, prev_results)
        if subprocess_params is None:
            return
        try:
            subprocess.run([r"python", script_path] + subprocess_params, check=True)
        except subprocess.CalledProcessError as e:
            pass


    elif cmd_list[0]=="open" or cmd_list[0]=="o":
        if len(cmd_list)>1 and (cmd_list[1]=='--help' or cmd_list[1]=='-h'):
            print("")
            print("open : open a file")     # tag_global_help
            print("")
            print("Usage:")
            print("  o [-c] [-e] [-n] [-v] [<index>|<activity_name>]")
            print("")
            print("Arguments:")
            print("  index : Open file by provideing the index from the previous search (default: 0).")
            print("  activity_name : Open file by providing the name of the activity.")
            print("")
            print("Options:")
            print("  -c  : Open in CMD (Command Prompt)")
            print("  -e  : Open in Windows Explorer")
            print("  -n  : Open in Notepad++")
            print("  -v  : Open in VS Code")
            print("")
            print("Note:")
            print("  If <index> is not provided, this command opens the first items from the list of the previous search results.")
            print("")
            return

        option_c = get_param_from_cli('-c', cmd_list)
        option_e = get_param_from_cli('-e', cmd_list)
        option_n = get_param_from_cli('-n', cmd_list)
        option_v = get_param_from_cli('-v', cmd_list)
        
        if not (option_c or option_e or option_n):  
            option_v = True     # Use -v as default application to open the activity

        if (len(cmd_list) == 1):
            cmd_list.append("0")  # If no index is provided, default to the first item in the previous search results

        if (len(cmd_list) == 2) and re.match("[0-9]+", cmd_list[1]):      # index is provided => select the corresponding activity
        
            if prev_results is None or len(prev_results)==0:
                print("ERROR: list of previous search results is not available")
                return

            index = int(cmd_list[1])
            if index > (len(prev_results)-1):
                print("ERROR: index out of range")
                return
            selected_result = prev_results[index]
            if selected_result["type"] == "kb":
                dir_path = selected_result["path"]
                file_path = os.path.join(dir_path, "description.md")
            elif selected_result["type"] == "1bf":
                dir_path = os.path.dirname(selected_result["path"])
                file_path = selected_result["path"]
            else:
                print(f"ERROR: selected item of type {selected_result['type']} cannot be opened")
                return
            

            if option_c:
                subprocess.call(["cmd", "/c", "start", "cmd", "/k", f"cd {dir_path}"])
            elif option_e:
                subprocess.call(["explorer", dir_path])
            elif option_n:
                subprocess.call([NOTEPADPP_PATH, file_path])
            elif option_v:
                open_in_vs_code(dir_path)
            return
        
        elif (len(cmd_list) == 2):      # activity's name is provided
            activity_name = cmd_list[1]
            activity_path = os.path.join(r"C:\dev0\kb0\activities", activity_name)
            if not os.path.isdir(activity_path):
                print(f"ERROR: cannot find activity '{activity_name}' in 'C:\\dev0\\kb0\\activities'")
                return
            
            if option_c:
                subprocess.call(["cmd", "/c", "start", "cmd", "/k", f"cd {activity_path}"])
            elif option_e:
                subprocess.call(["explorer", activity_path])
            elif option_n:
                subprocess.call([NOTEPADPP_PATH, os.path.join(activity_path, "description.md")])
            elif option_v:
                open_in_vs_code(activity_path)
            return
            
        print(f"ERROR: wrong parameters. Use '{cmd_list[0]} -h' for help.")


    elif cmd_list[0]=="pdf_to_text" or cmd_list[0]=="pdf":
        # pdf_to_text, pdf : Convert PDF files to text.   # tag_global_help
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf_to_text.py")
        subprocess_params = replace_numeric_indices_with_titles(cmd_list, prev_results)
        if subprocess_params is None:
            return
        try:
            subprocess.run([r"python", script_path] + subprocess_params, check=True)
        except subprocess.CalledProcessError as e:
            pass


    elif cmd_list[0]=="pull_request" or cmd_list[0]=="pr":
        if len(cmd_list)>1 and (cmd_list[1]=='--help' or cmd_list[1]=='-h'):
            print("")
            print("pr : review a pull-request")     # tag_global_help
            print("")
            print("Usage:")
            print("  pull_request [-r]")
            print("")
            print("Options:")
            print("  --review, -r  : Start the review")
            print("")
            print("Steps:")
            print("  1. Open a terminal in the cloned repo")
            print("  2. Open the Bitbucket 'Commits' page, and copy the full content in the clipboard (Ctrl-A Ctrl-V)")
            print("  3. In qqOne, run the command 'pr' (qqOne will open VS Code)")
            print("  4. In the terminal, paste the commands created by qqOne (they are already in the clipboard)")
            print("  5. Switch to VS Code and ask the questions")
            print("")
            return

        option_r = get_param_from_cli('--review', cmd_list) or get_param_from_cli('-r', cmd_list)

        if not option_r:
            print(f"ERROR: wrong parameters. Use '{cmd_list[0]} -h' for help.")
            return

        print("\n1. Open the Bitbucket 'Commits' page, and copy the full content in the clipboard (Ctrl-A Ctrl-V)")
        answer = input("2. Press Enter when done (or 'q' to quit).").strip()
        if answer.lower() == 'q':
            return

        clipboard_content = pyperclip.paste()
        git_hash_pattern = r'\b[a-f0-9]{8,40}\b'
        git_hashes = re.findall(git_hash_pattern, clipboard_content, re.IGNORECASE)
        if not git_hashes:
            print("ERROR: No git hashes found in clipboard content. Make sure the copied text contains the relevant git hashes.")
            return
        if len(git_hashes) >= 2:
            # Use first and last hash for range diff
            start_hash = git_hashes[-1]
            end_hash = git_hashes[0]
            git_command = f"git diff {start_hash}..{end_hash}"
        elif len(git_hashes) == 1:
            # Show diff for single commit
            git_command = f"git show {git_hashes[0]}"

        print(f"\nDetected git hashes: {git_hashes}")

        shell_commands = "\ngit pull"
        shell_commands += f"\n@echo. > {PR_REVIEW_DIFF_FILE}"
        shell_commands += f"\n@echo Describe the content of this pull-request >> {PR_REVIEW_DIFF_FILE}"
        shell_commands += f"\n@echo. >> {PR_REVIEW_DIFF_FILE}"
        shell_commands += f"\n{git_command} >> {PR_REVIEW_DIFF_FILE}"
        shell_commands += "\n"

        print(f"\nCommands to be executed in the terminal:")

        print(f"{shell_commands}")

        pyperclip.copy(shell_commands.replace('\n', '\r\n'))

        print("3. Open a terminal in the cloned repo")
        print("4. Paste the commands to the terminal (they are already in the clipboard)")
        answer = input("5. Press Enter when done (or 'q' to quit).").strip()
        if answer.lower() == 'q':
            return
        
        modified_files = []
        with open(PR_REVIEW_DIFF_FILE, 'r', encoding='utf-8', errors='replace') as f:
          lines = f.readlines()
        for line in lines:
            match = re.match(r'^diff --git a/(.+) b/.*', line)
            if match:
                modified_files.append(match.group(1))


        print(f"\nModified files: {modified_files}")
        shell_commands = ""
        for mod_file in modified_files:
            mod_file = mod_file.replace('/', '\\')  # Convert to Windows path
            shell_commands += f"\ncopy {mod_file} {PR_REVIEW_DIR}\\{os.path.basename(mod_file)}"
        shell_commands += "\n"

        print(f"\nCommands to be executed in the terminal:")

        print(f"{shell_commands}")

        pyperclip.copy(shell_commands.replace('\n', '\r\n'))

        print("5. Open a terminal in the cloned repo")
        print("6. Paste the commands to the terminal (they are already in the clipboard)")
        answer = input("7. Press Enter when done (or 'q' to quit).").strip()
        if answer.lower() == 'q':
            return

        print(f"\nFiles collected in: {PR_REVIEW_DIR}\n")
        answer = input("Enter 'y' to open the folder in VS Code.").strip()
        if answer.lower() == 'y':
            open_in_vs_code(PR_REVIEW_DIR)

        return


    elif cmd_list[0]=="quit" or cmd_list[0]=="q":
        if len(cmd_list)>1 and (cmd_list[1]=='--help' or cmd_list[1]=='-h'):
            print("")
            print("quit, q : close this console session.")     # tag_global_help
            print("")
            return
        # Save history before exiting
        history_commands = []
        for i in range(1, readline.get_current_history_length() + 1):
            if readline.get_history_item(i) not in ('h', 'help', 'q', 'quit'):
                history_commands.append(readline.get_history_item(i))
        with open(HISTORY_FILE_PATH, 'w') as f:
            for cmd in history_commands[-1000:]:  # Save last 1000 commands
                f.write(cmd + '\n')
        sys.exit(0)


    elif cmd_list[0]=="file" or cmd_list[0]=="f":
        if len(cmd_list)>1 and (cmd_list[1]=='--help' or cmd_list[1]=='-h'):
            print("")
            print("file, f : Search for files in the knowledge base")  # tag_global_help
            print("")
            print("Usage:")
            print("  f [--all] [-l] [-o] [-r] [-w] <indexes | pattern>")
            print("")
            print("Arguments:")
            print("  indexes : Open the file with the specified index from the previous search results")
            print("            Example:")
            print("            f 12        - open file 12 from previous search")
            print("  pattern : Show the files that match the specified regex pattern")
            print("            Examples:")
            print("            f castipy - list all activities with 'Castipy' in the title")
            print("")
            print("Options:")
            print("  --all : Search in the full knowledge base")
            print("  -o    : (Open) Open the file in VS Code")
            print("  -r    : (Recent) Show the 20 most recent files added to the knowledge-base (starts from the latest added)")
            print("  -l    : Generates a Large context file (size limit is increased from 200k to 500k)")
            print("  -w    : Whole Word (pattern must match a whole word)")
            return

        option_all = get_param_from_cli('--all', cmd_list)
        option_l   = get_param_from_cli('-l', cmd_list)
        option_o   = get_param_from_cli('-o', cmd_list)
        option_r   = get_param_from_cli('-r', cmd_list)
        option_w   = get_param_from_cli('-w', cmd_list)

        # Load all the 'text_bases' files
        text_base_paths = []
        if option_all:
            kb0_base_dir_list = [r"C:\dev0\kb0"]
        else:
            kb0_base_dir_list = [
                r"C:\dev0\kb0\activities",
            ]
        for search_dir in kb0_base_dir_list:
            for root, dirs, files in os.walk(search_dir):
                for file in files:
                    if (file.endswith(".md") or file.endswith(".txt")) and "readme." not in file.lower():
                        text_base_paths.append(os.path.join(root, file))

        if option_r:
            # Show the 20 most recent files added to the text-base (starts from the latest added)
            text_base_paths_sorted = sorted(text_base_paths, key=lambda p: os.path.getmtime(p), reverse=True)
            text_base_paths = text_base_paths_sorted[:20]
            prev_results = [{"title": os.path.basename(p), "type": "kb", "path": p, "size": get_activity_size(p)} for p in text_base_paths]
            print_results_to_console(prev_results)
            return

        max_size = 200_000 if option_l else 500_000

        if len(cmd_list) == 1:
            # 'f' (without parameters): print all the 'text_bases'
            prev_results = [{"title": os.path.basename(p), "type": "kb", "path": p, "size": get_activity_size(p)} for p in text_base_paths]
            print_results_to_console(prev_results)

        elif (len(cmd_list) == 2) and re.match("[0-9]+", cmd_list[1]):      # cmd_list[1] is an index
            # 'f <index>': open the file with the specified index from the previous search results
            index = int(cmd_list[1])
            if index > (len(prev_results)-1):
                print("ERROR: index out of range")
                return
            selected_result = prev_results[index]
            if selected_result["type"] != "kb":
                print("ERROR: selected item is not a text base")
                return
            assert os.path.isfile(selected_result["path"])
            print(f"Context File: {os.path.basename(selected_result['path'])} ({int(os.path.getsize(selected_result['path'])/1024)} kB)")
            if option_o:
                shutil.copy(selected_result['path'], DYNAMIC_CONTEXT_FILE)
                open_in_vs_code(max_size=max_size)
            else:
                print("(use the option '-o' to open it in VS Code)\n")

        elif len(cmd_list) == 2:    # cmd_list[1] is a regex
            # 'f <regex>': show the files that match the specified regex
            regex = re.compile(cmd_list[1], re.IGNORECASE)
            text_base_paths = [f for f in text_base_paths if regex.search(f)]
            if len(text_base_paths)==0:
                print(f"ERROR: Cannot find a text base that matches the regex '{cmd_list[1]}'")
                return
            else:
                prev_results = [{"title": os.path.basename(p), "type": "kb", "path": p, "size": get_activity_size(p)} for p in text_base_paths]
                print_results_to_console(prev_results)

        else:
            print(f"ERROR: wrong parameters. Use '{cmd_list[0]} -h' for help.")
            return

        return      # to not print command duration
    

    elif cmd_list[0]=="other_commands" or cmd_list[0]=="oc":
        if len(cmd_list)>1 and (cmd_list[1]=='--help' or cmd_list[1]=='-h'):
            print("")
            print("other_commands, oc : collection of other commands")   # tag_global_help
            print("")
            print("Usage:")
            print("  oc <activity>")
            print("")
            print("Arguments:")
            print("  activity : (optional) Activity addressed by the command.")
            print("")
            print("Options:")
            print("  --create_1bfs : Create 1BFs for the specified activity (if not specified, the command is applied to the whole knowledge base)")
            print("  --mermaid_to_images : Convert mermaid diagrams to images (needed to import markdown files to Confluence)")
            print("")
            return


    elif cmd_list[0]=="update" or cmd_list[0]=="u":
        if len(cmd_list)>1 and (cmd_list[1]=='--help' or cmd_list[1]=='-h'):
            print("")
            print("update, u : Update knowledge-base according to the configuration.")  # tag_global_help
            print("")
            print("Usage:")
            print("  u [-b] [-p] [<pattern>]")
            print("")
            print("Options:")
            print("  -b [<pattern>] : Update the qqOne knowledge-bases. <pattern> specifies the file to be taken from Downloads")
            print("  -p  : Update the qpDoc files")
            return

        option_b = get_param_from_cli('-b', cmd_list)
        option_p = get_param_from_cli('-p', cmd_list)
        
        pattern = cmd_list[1] if len(cmd_list)>1 else None
        
        if pattern:
            script_path = os.path.abspath(__file__)
            
            subprocess.run(['python', os.path.join(os.path.dirname(script_path), "create_1bfs.py"), pattern], check=True)
            return

        if option_b:
            subprocess.run([r"C:\dev0\qqone\update_files.bat"] + cmd_list[1:], check=True)

        if option_p:
            subprocess.run([r"C:\dev0\qpdoc\update_files.bat"], check=True)

        return      # to not print command duration

    else:
        print("ERROR: unkown commmand '%s'" % cmd)


def xml_get_formatted_text(item, prop_name):
    prop_value = item.find(prop_name)
    if prop_value is not None:
        text = list()
        for child in prop_value:
            text.append(ET.tostring(child, encoding='unicode', method='text'))
        if len(text):
            return("\\n".join(text).replace('@@@@', '&'))
        return(prop_value.text.replace('@@@@', '&'))
    return("None")


def xml_get_labels(item, prop_name):
    prop_value = item.find(prop_name)
    if prop_value is not None:
        return(','.join([child.text for child in prop_value]))
    return("None")


def xml_get_links(item, prop_name):
    links = list()
    issuelinks = item.find(prop_name)
    if issuelinks is not None:
        for issuelinktype in issuelinks:
            name = issuelinktype.find('name')
            if name is not None:
                if name.text=='Cloners':
                    continue
                outwardlinks = issuelinktype.find('outwardlinks')
                if outwardlinks is not None:
                    for issuelink in outwardlinks:
                        issuekey = issuelink.find('issuekey')
                        if issuekey is not None:
                            links.append(f"{name.text} {issuekey.text}")
                inwardlinks = issuelinktype.find('inwardlinks')
                if inwardlinks is not None:
                    for issuelink in inwardlinks:
                        issuekey = issuelink.find('issuekey')
                        if issuekey is not None:
                            reverse_link_name = f"(in){name.text}"
                            if name.text=='Implements':
                                reverse_link_name = 'Is Implemented By'
                            if name.text=='Consists (Bundle)':
                                reverse_link_name = 'Includes'
                            links.append(f"{reverse_link_name} {issuekey.text}")
        if links:
            return(', '.join(links))
    return("None")


def xml_get_text(item, prop_name):
    prop_value = item.find(prop_name)
    if prop_value is not None:
        text = prop_value.text
        if text:
            text = text.replace('@@@@', '&')
            return(text)
    return("None")


sys.excepthook = excepthook

load_dotenv()
NOTEPADPP_PATH = os.getenv("NOTEPADPP_PATH")
assert NOTEPADPP_PATH, "ERROR: NOTEPADPP_PATH environment variable is not set. Please set it to the path of Notepad++ executable."
DYNAMIC_CONTEXT_PY_PATH = os.path.join(os.path.dirname(__file__), 'dynamic_context.py')
TEMPORARY_DIR = os.getenv("TEMPORARY_DIR")
if not TEMPORARY_DIR:
    TEMPORARY_DIR = os.environ.get('TEMP')
if not TEMPORARY_DIR:
    TEMPORARY_DIR = os.path.dirname(__file__)

DYNAMIC_CONTEXT_DIR = os.path.join(TEMPORARY_DIR, 'dynamic_context')
DYNAMIC_CONTEXT_FILE = os.path.join(DYNAMIC_CONTEXT_DIR, 'dynamic_context.1bf.txt')
os.makedirs(DYNAMIC_CONTEXT_DIR, exist_ok=True)

PR_REVIEW_DIR = os.path.join(TEMPORARY_DIR, 'pr_review')
PR_REVIEW_DIFF_FILE = os.path.join(PR_REVIEW_DIR, 'pr_review_diff.txt')
if os.path.exists(PR_REVIEW_DIR):
    shutil.rmtree(PR_REVIEW_DIR)
os.makedirs(PR_REVIEW_DIR)

JIRA_EXPORT_DIR = os.path.join(TEMPORARY_DIR, 'jira_export')
JIRA_EXPORT_FILE = os.path.join(JIRA_EXPORT_DIR, 'jira_export.gitignore.xml')
os.makedirs(JIRA_EXPORT_DIR, exist_ok=True)

HISTORY_FILE_PATH = os.path.join(TEMPORARY_DIR, "qqone_history.txt")

commands = []
script_path = os.path.abspath(__file__)
with open(script_path, 'r', encoding='utf-8') as file:
    current_script_content = file.readlines()
for line in current_script_content:
    match = re.search(r'^    (if|elif) cmd_list\[0\]=="([^"]*)".*', line)
    if match:
        commands.append(match.group(2))

completer = MyCompleter(commands)

readline.set_completer(completer.complete)
readline.parse_and_bind('tab: complete')

# Load the history
history_commands = []
if os.path.exists(HISTORY_FILE_PATH):
    with open(HISTORY_FILE_PATH, 'r') as f:
        history_commands = [line.strip() for line in f if line.strip()]
for cmd in history_commands[:1000]:
    readline.add_history(cmd)

while True:
    run(input("qqOne>").strip())

# import pdb; pdb.set_trace()
