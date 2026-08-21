# Script: usebm25.py
# Description: Use BM25 to search for a given query in .txt files
# Usage: python usebm25.py "query"
#
# Parameters:
#   query - String to be searched
#
# Examples:
#   python usebm25.py "search term"
#   python usebm25.py "multi word query" -v

import argparse
import sys
import os
from pathlib import Path
from rank_bm25 import BM25Okapi


common_words_to_ignore = ['shall', 'none', 'document', 'documentation', 'describe', 'described', 'describes']

config = None

def excepthook(type, value, tb):
    import traceback, pdb
    traceback.print_exception (type, value, tb)
    print
    pdb.pm ()


def get_txt_files(directory):
    """Get all .txt files in the directory recursively"""
    txt_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.txt'):
                txt_files.append(os.path.join(root, file))
    return txt_files


def tokenize(text):
    """Simple tokenization: lowercase and split by whitespace"""
    return text.lower().split()


def search_bm25(query, directory, verbose=False, very_verbose=False):
    """Search in .txt files using BM25"""
    
    # Get all txt files
    txt_files = get_txt_files(directory)
    
    if not txt_files:
        print(f"No .txt files found in {directory}")
        return []
    
    if verbose or very_verbose:
        print(f"Found {len(txt_files)} .txt files")
    
    # Read and tokenize documents
    documents = []
    file_mapping = {}  # Map document index to filepath
    
    for filepath in txt_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                tokens = tokenize(content)
                documents.append(tokens)
                file_mapping[len(documents) - 1] = filepath
                
                if very_verbose:
                    print(f"Loaded: {filepath} ({len(tokens)} tokens)")
        except Exception as e:
            if verbose or very_verbose:
                print(f"Error reading {filepath}: {e}")
            continue
    
    if not documents:
        print("No documents could be loaded")
        return []
    
    # Initialize BM25
    bm25 = BM25Okapi(documents)
    
    # Tokenize query
    query_tokens = tokenize(query)
    
    if verbose or very_verbose:
        print(f"Searching for: {query_tokens}")
    
    # Get scores
    scores = bm25.get_scores(query_tokens)
    
    # Create results list with scores and filenames
    results = []
    for doc_idx, score in enumerate(scores):
        if score > 0:  # Only include documents with positive score
            results.append({
                'filepath': file_mapping[doc_idx],
                'score': score,
                'filename': os.path.basename(file_mapping[doc_idx])
            })
    
    # Sort by score (descending)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results




def parse_arguments():
    parser = argparse.ArgumentParser(description="Search .txt files using BM25 algorithm in a given directory.")
    parser.add_argument("question", type=str, help="Mandatory parameter: the search query.")
    parser.add_argument("-v", action="store_true", help="Verbose console output")
    parser.add_argument("-vv", action="store_true", help="Very Verbose console output")

    return parser.parse_args()




if __name__ == "__main__":

    sys.excepthook = excepthook

    args = parse_arguments()

    kb1 = "/Users/carlocamicia/kb1/DTech"

    # Verify directory exists
    if not os.path.exists(kb1):
        print(f"Error: Directory {kb1} does not exist")
        sys.exit(1)

    # Perform BM25 search
    results = search_bm25(
        args.question, 
        kb1, 
        verbose=args.v,
        very_verbose=args.vv
    )

    # Display results
    if results:
        print(f"\nFound {len(results)} matching document(s):\n")
        for idx, result in enumerate(results, 1):
            if idx>10:  # Limit to top 10 results
                break
            print(f"{idx}. {result['filename']}")
            print(f"   Path: {result['filepath']}")
            print(f"   BM25 Score: {result['score']:.4f}\n")
    else:
        print(f"No matches found for query: {args.question}")

# import pdb; pdb.set_trace()