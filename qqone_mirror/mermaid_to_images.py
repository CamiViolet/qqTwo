"""
Script to convert Mermaid diagrams to PNG files. Needed to import markdown files to Confluence.
Uses the mermaid-py package for conversion.

Example:
    python mermaid_to_images.py sprtorcas_1737_certified_static_serializer
    python mermaid_to_images.py sprtorcas_1737_certified_static_serializer --skip_image_conversion --file raw/concept_css_confluence_page.gitignore.md
"""

import argparse
from html import parser
import re
import os
import sys
from pathlib import Path
from mermaid import Mermaid     # pip install mermaid-py
from library import excepthook, get_doc_properties2, load_config


def extract_mermaid_diagrams(md_file_path):
    """
    Extract all Mermaid diagrams from a markdown file.
    
    Args:
        md_file_path: Path to the markdown file
        
    Returns:
        List of tuples containing (diagram_name, mermaid_code)
    """
    if ".ignore." in md_file_path.name.lower():
        return [], ""
    
    with open(md_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Pattern to match mermaid code blocks with optional titles
    pattern = r'```mermaid\s*(?:---\s*title:\s*([-\w]+)\s*---\s*)?(.*?)```'
    matches = re.finditer(pattern, content, re.DOTALL)

    doc_properties = get_doc_properties2(str(md_file_path))

    confluence_page_id = doc_properties.get("confluence_page_id", None)
    
    diagrams = []
    modified_content = content
    for i, match in enumerate(matches):
        if not confluence_page_id:
            print(f"INFO: No Confluence page ID found for {md_file_path.name}; skipping page.")
            continue
        title = match.group(1)
        code = match.group(2)
        # Use title if available, otherwise use index-based name
        diagram_name = title if title else f"diagram_{i+1}"
        diagrams.append((diagram_name, code.strip()))

        url = f"https://confluence.tttech.com/download/attachments/" \
            + f"{confluence_page_id[0]}/" \
            + f"{diagram_name}.png?api=v2"
        
        md_include = f"![{diagram_name}]({url})"
        
        # Replace the full match with md_include
        modified_content = modified_content.replace(match.group(0), md_include)
    
    return diagrams, modified_content


def convert_to_png(diagram_name, mermaid_code, output_dir):
    """
    Convert a Mermaid diagram to PNG file.
    
    Args:
        diagram_name: Name for the output file (without extension)
        mermaid_code: Mermaid diagram code
        output_dir: Directory to save the PNG file
    """

    output_path = os.path.join(output_dir, f"{diagram_name}.png")
    
    try:
        # Create Mermaid object and render to PNG
        mermaid = Mermaid(mermaid_code)
        mermaid.to_png(output_path)
        return True
    except Exception as e:
        print(f"Error converting {diagram_name}: {str(e)}")
        return False


def parse_arguments():
    parser = argparse.ArgumentParser(description="Script to convert Mermaid diagrams to PNG files.")
    parser.add_argument("activity", help="Generate the 1bf only for the specified topic")
    parser.add_argument("--file", help="Relative path of a specific markdown file to process (relative to the activity directory)")
    parser.add_argument("--skip_image_conversion", action="store_true", help="Skip actual image conversion; only extract diagrams and generate markdown references")
    parser.add_argument("-v", action="store_true", help="Verbose console output")

    return parser.parse_args()


def main():
    
    sys.excepthook = excepthook

    args = parse_arguments()

    config = load_config('kb0')

    kb_path = config['kb_config']['kb_path']

    activity_dir = os.path.join(kb_path, "activities", args.activity)

    if not os.path.isdir(activity_dir):
        print(f"ERROR: Activity {activity_dir} does not exist.")
        sys.exit(1)
    
    # Find all markdown files in the directory
    if args.file:
        specific_file = Path(activity_dir) / args.file
        if not specific_file.is_file():
            print(f"ERROR: File {specific_file} does not exist.")
            sys.exit(1)
        md_files = [specific_file]
    else:
        md_files = list(Path(activity_dir).glob("*.md"))
    
    # Process each markdown file
    for md_file_path in md_files:
        # Extract all Mermaid diagrams
        diagrams, modified_content = extract_mermaid_diagrams(md_file_path)
        
        if diagrams:
            print(f"File {md_file_path.name} contains {len(diagrams)} Mermaid diagram(s). Converting to PNG...")
        
        # Create output directory for this file's diagrams
        file_output_dir = os.path.join(activity_dir, "confluence_page.gitignore", "diagrams")
        os.makedirs(file_output_dir, exist_ok=True)
        file_output_dir = os.path.join(file_output_dir, md_file_path.stem)
        
        # Convert each diagram to PNG
        if not args.skip_image_conversion:
            for diagram_name, mermaid_code in diagrams:
                os.makedirs(file_output_dir, exist_ok=True)
                print(f"- Converting: {diagram_name}")
                convert_to_png(diagram_name, mermaid_code, file_output_dir)
        
        # Create modified markdown file with PNG references
        if len(diagrams) > 0:
            new_md_path = os.path.join(activity_dir, "confluence_page.gitignore")
            os.makedirs(new_md_path, exist_ok=True)
            new_md_path = os.path.join(new_md_path, md_file_path.name)
            with open(new_md_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            print(f"Created file {new_md_path}")


if __name__ == "__main__":
    main()
