# Script: in_text_keywords.py
# Description: Collect the keywords that are explicitly set by the author in the documents.
#              The script generates the file in_text_keywords.json
# Usage: python in_text_keywords.py
#
# Parameters:
#
# Examples:
#   python in_text_keywords.py

import json
import math
import os
import re
import sys
import glob
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer


def excepthook(type, value, traceback):
    """Exception hook for debugging."""
    pass


def normalize(word):
    """
    Converts a word to lowercase and replaces dashes and slashes with underscores for consistent normalization.
    """
    norm_kw = word.lower()
    norm_kw = norm_kw.replace("/", "_")
    norm_kw = norm_kw.replace("-", "_")
    return(norm_kw)


def parse_keywords(line, titles):
    """
    Parse keywords from a line containing 'keywords', 'related', 'synonyms'.
    Handles comma-separated values with proper quote handling.
    Example:
    Keywords: AI
    Related: "data science", AI, ML, "deep-learning"
    Synonyms: "AI", 'artificial intelligence'
    """

    for title in titles:
        keywords_match = re.search(title.lower() + r':\s*(.*)', line, re.IGNORECASE)
        if keywords_match:
            keywords_text = keywords_match.group(1).strip()
            if keywords_text:
                break           
    
    if not keywords_text:
        return (None, None)
        
    keywords_text = keywords_text.lower()
    
    # Parse keywords handling quotes
    keywords = []
    current_keyword = ""
    in_quotes = False
    quote_char = None
    
    i = 0
    while i < len(keywords_text):
        char = keywords_text[i]
        
        if not in_quotes and char in ['"', "'"]:
            # Start of quoted string
            in_quotes = True
            quote_char = char
        elif in_quotes and char == quote_char:
            # End of quoted string
            in_quotes = False
            quote_char = None
        elif not in_quotes and char == ',':
            # End of current keyword
            if current_keyword.strip():
                keywords.append(current_keyword.strip())
            current_keyword = ""
            i += 1
            continue
        else:
            current_keyword += char
        
        i += 1
    
    # Add the last keyword
    if current_keyword.strip():
        keywords.append(current_keyword.strip())
    
    # Clean up quotes from keywords
    keywords_no_quotes = []
    for keyword in keywords:
        keyword = keyword.strip()
        if keyword.startswith('"') and keyword.endswith('"'):
            keyword = keyword[1:-1]
        elif keyword.startswith("'") and keyword.endswith("'"):
            keyword = keyword[1:-1]
        if keyword:
            keywords_no_quotes.append(keyword)

    normalized_keywords = [normalize(kw) for kw in keywords_no_quotes]

    return (title, normalized_keywords)


def main():
    sys.excepthook = excepthook
    
    files = []

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Collect the text files
    # topics_dir = os.path.join(base_dir, '..', 'kb0', 'activities', 'manual_comments')
    # topics_files = glob.glob(os.path.join(topics_dir, '**', '*.txt'), recursive=True)
    # topics_files += glob.glob(os.path.join(topics_dir, '**', '*.md'), recursive=True)
    # files.extend(topics_files)
    # 
    # files = [f for f in files if "readme." not in f.lower()]
    
    files = [r"C:\Dev_Analisys\kb0\activities\manual_comments\manual_comments.1bf.txt", ]
    
    '''
    Description:
    Keywords: Words or phrases that describe the topics, concepts, or themes of a document or section. 
    Related: Words or phrases that refer to associated or alternative topics, for example an alternative solution.
    Synonyms: Words or short phrases (usually up to two per line) that are interchangeable. Use one line for each group of synonyms.
    
    For example, the page "Comparison between MB++ and MBD"
    - Keywords: MBD, MB++
    - Related: MBD, IPCF (because both supports inter-host on shared memory, but the page is not about IPCF)
    - Synonyms: MB_Direct, MBD (they are equivalent)
    - Synonyms: MB++, MultiBuffer++, MBPP, MS_MBPP (they are equivalent)
    '''

    all_keywords = defaultdict(list)
    
    for file in files:
        file_name = os.path.basename(file)
        print(f"Processing file: {file_name}")
        
        with open(file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        
        for line_num, line_content in enumerate(lines):
            line = line_content.lower().strip()
            if "keywords:" in line or "related:" in line or "synonyms:" in line:
                if line.startswith('-'):
                    line = line[1:].strip()
                if line.startswith("keywords:") or line.startswith("related:") or line.startswith("synonyms:"):
                    title, keywords = parse_keywords(line, ['keywords', 'related', 'synonyms'])
                    if not keywords:
                        continue
                    if title=='synonyms' and len(keywords)<2:
                        print(f"ERROR: Synonyms line with less than 2 keywords found: {line_content.strip()}")
                        continue
                    all_keywords[title].append(keywords)

    output_dir = os.path.join(base_dir, '..', 'kb0')
    output_file = os.path.join(output_dir, 'in_text_keywords.json')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Save all_keywords to JSON file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_keywords, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {len(all_keywords)} keyword groups to: {output_file}")
    except Exception as e:
        print(f"Error saving to {output_file}: {e}")
    
    return all_keywords    
    
    
if __name__ == "__main__":
    main()

# import pdb; pdb.set_trace()
