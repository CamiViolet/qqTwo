'''
usage: context.py [-h] [-v]

options:
  -h, --help  show this help message and exit
  -v          Verbose console output

Examples:
    python context.py "What is the MCU Stack?"
'''

import argparse
import json
import glob
import os
import re
import sys
from collections import defaultdict
from library import get_doc_properties, load_config, excepthook, get_prop_names
from datetime import datetime


def extract_words(text):
    """
    Tokenizes the input text into words, including those with slashes, dashes, and underscores.
    """
    tokens = re.findall(r'\b[\w/_-]+\+\+|\b[\w/_-]+\b', text)
    return(tokens)
           

def get_kb_terms(documents):
    terms = dict()

    prop_names = get_prop_names()
    for doc in documents:
        for prop_name in prop_names:
            if prop_name not in doc:
                continue
            value = doc[prop_name]
            if prop_name in ['keywords', 'related', 'context']:
                assert type(value) == list
                if prop_name not in terms:
                    terms[prop_name] = defaultdict(int)
                for term in value:
                    terms[prop_name][term] += 1
            if prop_name in ['synonyms', 'alternatives']:
                assert type(value) == list
                if prop_name not in terms:
                    terms[prop_name] = []
                terms[prop_name].append(value)

    return terms

def get_patterns(question):
    # question = re.sub(r'\bpi\s+([0-9]{2}\.[0-9])\b', r'PI_\1', question_2, flags=re.IGNORECASE)
    # question = re.sub(r'[^a-zA-Z0-9\s/_-]', ' ', pre_proc_question)   # Remove non alpha-num

    # Tokenize
    words = extract_words(question)
    print(f"words : {words}")

    import pdb; pdb.set_trace()

    pass


def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate the 1bf (One Big File) for all the topics")
    parser.add_argument("topic_name", nargs="?", default=None, help="Generate the 1bf only for the specified topic (default: all topics)")
    parser.add_argument("-v", action="store_true", help="Verbose console output")
    parser.add_argument("-kb0", action="store_true", help="Use kb0 knowledge base 'MotionWise Classic Communication' (default)")
    parser.add_argument("-kb2", action="store_true", help="Use kb2 knowledge base 'Automotive Papers and Presentations (from Salva)'")
    parser.add_argument("question", type=str, help="Mandatory parameter: the question or pattern to be searched.")

    return parser.parse_args()


def extract_log_notes(log_file):
    documents = []
    note = []
    date = None

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.readlines()
    for i, line in enumerate(content):
        line = line.rstrip()
        indent = len(line) - len(line.lstrip(' '))
        if indent == 0:
            match = re.search(r'\b\d{2}[-/]\d{2}[-/]\d{4}\b', line)
            if match:
                try:
                    date = datetime.strptime(match.group(0), "%d/%m/%Y").date()
                except ValueError:
                    pass
                continue
        if len(line) > 0 and indent == 0:
            if note and len(note) > 0:
                documents.append({
                    'date': date.strftime("%Y/%m/%d") if date else None,
                    'title': note[0],
                    'type': 'log_note',
                    'text': note[1:]
                })
            note = None
            if re.search(r'#tag_[a-z_]+_base\b', line):
                line = re.sub(r'#tag_[a-z_]+_base\b', '', line)
                note = [line.rstrip()]     # Start a new note
        else:
            if note:
                ltrim = min(4, indent)
                note.append(line[ltrim:])

    return documents


def load_kb_documents(config):
    
    kb_path = config['kb_config']['kb_path']

    log_file = config['kb_config']['log_file']

    documents = extract_log_notes(log_file)

    # Load all markdown files in the knowledge base
    files = glob.glob(os.path.join(kb_path, '**', '*.md'), recursive=True)
    for file in files:
        with open(file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.readlines()
            documents.append({
                'file': file,
                'text': content
            })

    # Extract properties from all documents
    for doc in documents:
        properties = get_doc_properties(doc['text'])
        doc.update(properties)

    return documents


def main():
    sys.excepthook = excepthook

    args = parse_arguments()
    
    # Determine which knowledge base to use
    if args.kb2:
        kb_name = 'kb2'
    else:
        kb_name = 'kb0'  # Default to kb0
    
    config = load_config(kb_name)

    documents_path = os.path.join(config['kb_config']['kb_path'], "documents.json")
    with open(documents_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)

    #---------------------------------------------------------------------------
    # Extract the search patterns from the question
    # TODO: Normalize Pattern
    # TODO: Get all the terms (combination of words) (a phrase may contain one only word)
    # TODO: Search the terms in terms.json
    # TODO: The terms with less occurrences have weight 5 (rationale: if the question has multiple terms, the less common ones are more specific and hence more relevant)
    # TODO: The terms without matching have weight 1
    # TODO: We get a list of terms 
    # TODO: Each terms has synonyms, hence we have a list of lists
    # TODO: In the docs, Search in title, in keywords, in text 

    patterns = get_patterns(args.question)

    return


if __name__ == "__main__":
    main()

# import pdb; pdb.set_trace()
