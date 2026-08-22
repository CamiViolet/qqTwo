"""
Script to create a new activity in the knowledge base.

Examples:
    python new_activity.py
    python new_activity.py 'My New Activity'
"""

import glob
import os
import shutil
import re
import sys
from datetime import datetime
from dotenv import load_dotenv
from library import get_activity_date, get_activity_size, normalize_to_C_symbol, load_config


load_dotenv()


def _parse_glossary_entry(line):
    """Return (term, definition) for valid glossary entries, else (None, None)."""
    m = re.match(r'^-[\*\s]*([^:]+):[\*\s]*(.+)', line)
    term = m.group(1).strip() if m else None
    term = term.replace("**", "") if term else None
    definition = m.group(2).strip() if m else None
    return (term, definition)


def collect_glossary_contents(target_dir):
    # contents: term -> [activity_date, definition]
    contents = {}
    for activity_path, dirs, files in os.walk(target_dir):
        for file in files:
            if file.lower() == 'glossary.md':
                activity_date = get_activity_date(activity_path)
                if activity_date is None:
                    continue
                glossary_path = os.path.join(activity_path, file)
                try:
                    with open(glossary_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            term, definition = _parse_glossary_entry(line)
                            if term is None:
                                continue
                            existing = contents.get(term)
                            # Keep the entry from the most recently updated activity
                            if existing is None or (activity_date or '') > (existing[0] or ''):
                                contents[term] = [activity_date, definition]
                except Exception as e:
                    print(f"WARNING: Failed to read glossary file '{glossary_path}': {e}")
    lines = ["# Glossary: Acronyms, Technical Terms, and Entity Names"]
    lines.append("<!--")
    current_date = datetime.now().strftime("%Y-%m-%d")
    lines.append(f"updated: {current_date}")
    lines.append("-->\n")
    for term in sorted(contents, key=str.lower):
        activity_date, definition = contents[term]
        lines.append(f"- **{term}** : {definition}")
    return "\n".join(lines)


def create_new_activity(config, activity_name):

    kb_base_dir = config['kb_config']['kb_path']
    target_dir = os.path.join(kb_base_dir, 'activities')

    if not activity_name or activity_name.startswith('-'):  # If title is not available or not valid
        activity_name = input(f"\nEnter name of the activity (e.g. 'Validation Projects'): ").strip()

    title_normalized = normalize_to_C_symbol(activity_name).lower()

    new_activity_dir = os.path.join(target_dir, title_normalized)
    if os.path.exists(new_activity_dir):
        print(f"ERROR: Activity already exists: {new_activity_dir}")
        return(None)

    # Copy the template 'C:\dev0\kb0\activities\_template' to the new directory
    template_dir = os.path.join(target_dir, '_template')
    shutil.copytree(template_dir, new_activity_dir)
    os.makedirs(os.path.join(new_activity_dir, 'raw'), exist_ok=True)

    print(f"Created activity: {title_normalized}")

    current_date = datetime.now().strftime("%Y-%m-%d")

    glossary_contents = collect_glossary_contents(target_dir)

    # Load other 1bf_config.yaml files as examples
    examples_1bf_configs = ""

    # Fill placeholders in all markdown files
    for md_file in glob.glob(os.path.join(new_activity_dir, '*.md')):
        with open(md_file, 'r', encoding='utf-8') as fl:
            md_content = fl.read()
        md_content = md_content.replace("{updated}", current_date)
        md_content = md_content.replace("{title}", activity_name)
        with open(md_file, 'w', encoding='utf-8') as fl:
            fl.write(md_content)

    # Create the glossary.md
    glossary_file = os.path.join(new_activity_dir, 'glossary.md')
    with open(glossary_file, 'w', encoding='utf-8') as fl:
        fl.write(glossary_contents)

    # Fill the 1bf_config.yaml
    config_file = os.path.join(new_activity_dir, '1bf_configs', '1bf_config.yaml')
    with open(config_file, 'r', encoding='utf-8') as fl:
        config_content = fl.read()
    config_content = config_content.replace("{date}", current_date)
    config_content = config_content.replace("{title}", activity_name)
    config_content = config_content.replace("{title_normalized}", title_normalized)
    config_content = config_content.replace("{examples}", examples_1bf_configs)
    with open(config_file, 'w', encoding='utf-8') as fl:
        fl.write(config_content)

    results = [{"title": activity_name, "type": "kb", "path": new_activity_dir, "size": get_activity_size(new_activity_dir)}]
    return(results)


def main(cmd_line_args):
    activity_name = cmd_line_args[0] if cmd_line_args else None

    config = load_config()

    return create_new_activity(config, activity_name)


if __name__ == '__main__':
    main(sys.argv[1:])

# import pdb; pdb.set_trace()
