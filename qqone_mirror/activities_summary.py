'''
usage: activities_summary.py [-h] [-v]

Create a summary of all the activities of the knowledge base.

options:
  -h, --help  show this help message and exit
  -v          Verbose console output
  '''

import argparse
import json
import glob
import os
import re
import sys
from collections import defaultdict
from library import load_json, doc_properties, load_config, excepthook


global config


def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate the 1bf (One Big File) for all the topics")
    parser.add_argument("topic_name", nargs="?", default=None, help="Generate the 1bf only for the specified topic (default: all topics)")
    parser.add_argument("-v", action="store_true", help="Verbose console output")

    return parser.parse_args()


def main():
    global config
    
    sys.excepthook = excepthook

    args = parse_arguments()

    config = load_config('kb0')

    kb_path = config['kb_config']['kb_path']

    description_files = glob.glob(os.path.join(kb_path, "**", "description.md"), recursive=True)
    description_files += glob.glob(os.path.join(kb_path, "**", "description.txt"), recursive=True)

    # Create the file config_example.gitignore.json with the content of all the config files.
    activity_summary = defaultdict(dict)
    for description_file in description_files:
        activity_path = os.path.dirname(description_file)
        activity_name = os.path.basename(activity_path)

        with open(description_file, 'r', encoding='utf-8', errors='replace') as f:
            description_content = f.read()
            description_content = description_content.strip(' \n')
            activity_summary[activity_name]['description'] = description_content

        # Search for config*.json files in activity_path (no subdirectories)
        config_files = glob.glob(os.path.join(activity_path, "config*.json"))
        updated_list = []
        for config_file in config_files:
            activity_config = load_json(config_file)
            updated = activity_config.get('updated')
            if updated:
                updated = updated.replace('/', '-').strip()
                # Print an error if the date is not in the format YYYY-MM-DD or YYYY-MM-DD HH:MM:SS
                if re.match(r'^\d{4}-\d{2}-\d{2}\s*.*$', updated):
                    updated_list.append(updated)
                else:
                    print(f"ERROR: Invalid date format in {config_file}: {updated}. Expected format: YYYY-MM-DD or YYYY-MM-DD HH:MM")
        # Keep only the latest update date
        updated_list.sort(key=lambda d: d.ljust(16), reverse=True)
        if updated_list:
            activity_summary[activity_name]['updated'] = updated_list[0]

    # Sort the activity summary by activity date (latest first) 
    activity_summary = dict(sorted(activity_summary.items(), key=lambda item: item[1].get('updated', ''), reverse=True))

    activity_summary_str = "\nSummary of all the activities:\n\n"
    for activity_name, activity_info in activity_summary.items():
        activity_summary_str += f"Activity: {activity_name}\n"
        description = activity_info.get('description', '').replace('\n', '\n    ')
        activity_summary_str += f"    Description: {description}\n"
        activity_summary_str += f"    Last Updated: {activity_info.get('updated', '')}\n"
        activity_summary_str += "\n"

    activity_summary_path = os.path.join(kb_path, "activities_summary.txt")
    with open(activity_summary_path, 'w', encoding='utf-8', errors='replace') as f:
        f.write(activity_summary_str)
    if args.v:
        print(f"Created example file with the content of all the config files: {activity_summary_path}")

    return


if __name__ == "__main__":
    main()

# import pdb; pdb.set_trace()
