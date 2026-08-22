"""
Script to search/list activities in the knowledge base.

Examples:
    python find_activities.py
    python find_activities.py -r
    python find_activities.py castipy
    python find_activities.py castipy,nanopb
"""

import argparse
import glob
import os
import re
import subprocess
import sys
from dotenv import load_dotenv
from library import get_activity_size, get_activity_date, load_config, print_results_to_console


load_dotenv()
NOTEPADPP_PATH = os.getenv("NOTEPADPP_PATH")
TEMPORARY_DIR = os.getenv("TEMPORARY_DIR") or os.environ.get('TEMP') or os.path.dirname(os.path.abspath(__file__))
KB0_ACTIVITIES_DIR = r"C:\dev0\kb0\activities"


def search_full_text(patterns, whole_word=False):
    """Search for patterns in all markdown files within activities.
    
    Returns list of activities (directories) that contain matches, not individual files.
    Each activity includes a count of total pattern occurrences.
    """
    if whole_word:
        regexes = [re.compile(r'\b' + p + r'\b', re.IGNORECASE) for p in patterns]
    else:
        regexes = [re.compile(p, re.IGNORECASE) for p in patterns]
    
    matched_activities = {}  # Dictionary: activity_dir -> occurrence count
    
    for root, dirs, files in os.walk(KB0_ACTIVITIES_DIR):
        if root == KB0_ACTIVITIES_DIR:  # Ignore root-level files i.e. files that are not in an activity
            continue
        for file in files:
            if file.lower().endswith('.md'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    # Count occurrences for all regexes in this file
                    occurrence_count = sum(len(rx.findall(content)) for rx in regexes)
                    if occurrence_count > 0:
                        # Find the activity directory (the one containing 'description.md')
                        activity_dir = root
                        while activity_dir and not os.path.exists(os.path.join(activity_dir, 'description.md')):
                            activity_dir = os.path.dirname(activity_dir)
                        if activity_dir and os.path.exists(os.path.join(activity_dir, 'description.md')):
                            matched_activities[activity_dir] = matched_activities.get(activity_dir, 0) + occurrence_count
                except Exception as e:
                    print(f"WARNING: Failed to read file '{file_path}': {e}")
    
    if not matched_activities:
        return None
    
    results = [{"title": os.path.basename(p), "type": "kb", "path": p, "size": get_activity_size(p), "count": matched_activities[p]} for p in sorted(matched_activities.keys())]

    results = sorted(results, key=lambda x: x['count'], reverse=True)  # Sort by occurrence count descending

    return results


def open_in_vs_code(path, max_size=200_000):
    subprocess.Popen(
        [r"C:\Users\nxg18988\AppData\Local\Programs\Microsoft VS Code\Code.exe", "--reuse-window", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True
    )


def get_activities():
    """Return list of activity directory paths from the knowledge base."""
    activities = []
    for root, dirs, files in os.walk(KB0_ACTIVITIES_DIR):
        for file in files:
            if file == "description.md":
                activity = os.path.dirname(os.path.join(root, file))
                if os.path.basename(os.path.dirname(activity)) != "activities":
                    print(f"ERROR: 'description.md' files are used to define activities, but the file '{file}' is not in an 'activities' folder. Please rename it or move it to the correct location.")
                    sys.exit(1)
                activities.append(activity)
    return activities


def parse_arguments(cmd_line_args):
    parser = argparse.ArgumentParser(
        prog='a',
        description="Search and list activities in the knowledge base.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  a                       list all activities\n"
            "  a -r                    show 20 most recently modified activities\n"
            "  a castipy               list activities matching 'castipy'\n"
            "  a castipy,nanopb        list activities matching 'castipy' OR 'nanopb'\n"
        ),
    )
    parser.add_argument('patterns', nargs='?', help='Comma-separated regex patterns to filter activity titles')
    parser.add_argument('-l', action='store_true', help='large context (increases size limit from 200k to 500k)')
    parser.add_argument('-r', action='store_true',  help='show the 20 most recently modified activities')
    parser.add_argument('-w', action='store_true',  help='whole word matching for patterns')
    parser.add_argument('-f', '--full-text', action='store_true', help='search for patterns in all markdown files (full text search)')

    try:
        args = parser.parse_args(cmd_line_args)
    except SystemExit:
        return None  # or handle it however you need
    return args


def main(cmd_line_args):

    args = parse_arguments(cmd_line_args)

    if args is None:
        return

    config = load_config()

    activities = get_activities()   # 'activities' is a list of directories as full paths, e.g. 'C:\dev0\kb0\activities\castipy'

    if args.r:
        updates = []
        for activity_path in activities:
            activity_name = os.path.basename(activity_path)
            if activity_name == "_template":
                continue
            activity_updated_on = get_activity_date(activity_path)
            if activity_updated_on:
                updates.append([activity_updated_on, activity_path])
        updates_sorted = sorted(updates, key=lambda x: x[0], reverse=True)
        updates = updates_sorted[:20]
        results = [{"title": os.path.basename(p), "type": "kb", "path": p, "size": get_activity_size(p)} for _, p in updates]
        if not results:
            print(f"ERROR: Cannot find activities matching the pattern '{args.patterns}' in markdown files")
        return(results)

    max_size = 500_000 if args.l else 200_000

    if not args.patterns:
        # No argument: list all activities
        results = [{"title": os.path.basename(p), "type": "kb", "path": p, "size": get_activity_size(p)} for p in activities]
        if not results:
            print(f"ERROR: No activity found")
        return(results)

    # Full text search in markdown files
    if args.full_text:
        patterns = [p.strip() for p in args.patterns.split(',')]
        results = search_full_text(patterns, whole_word=args.w)
        if not results:
            print(f"ERROR: Cannot find activities matching the pattern '{args.patterns}' in markdown files")
        return(results)

    # Try exact name match first (happens when qqOne resolves an index to a title)
    activity_path = next((a for a in activities if os.path.basename(a) == args.patterns), None)
    if activity_path:     # if exact match
        activity_name = os.path.basename(activity_path)
        print(f"Activity: {activity_name}")
        results = [{"title": activity_name, "type": "kb", "path": activity_path, "size": get_activity_size(activity_path)}]
        return(results)

    # Treat as comma-separated regex patterns
    patterns = [p.strip() for p in args.patterns.split(',')]
    if args.w:
        regexes = [re.compile(r'\b' + p + r'\b', re.IGNORECASE) for p in patterns]
    else:
        regexes = [re.compile(p, re.IGNORECASE) for p in patterns]
    filtered = [f for f in activities if any(rx.search(os.path.basename(f)) for rx in regexes)]
    if not filtered:
        print(f"ERROR: Cannot find a text base that matches the regex '{args.patterns}'")
        return(None)
    results = [{"title": os.path.basename(p), "type": "kb", "path": p, "size": get_activity_size(p)} for p in filtered]
    return(results)

if __name__ == '__main__':
    main(sys.argv[1:])

# import pdb; pdb.set_trace()
