# Script: dynamic_context.py
# Description: Create a dynamic context (1bf - One Big File) by using the input parameter
# Usage: python dynamic_context.py pattern
#
# Parameters:
#   pattern - String to be searched (regex)
#
# Examples:
#   python dynamic_context.py -L1 "smoke.?test" 100

import argparse
import os
import json
import re
import sys
from collections import defaultdict
import glob
from sklearn.feature_extraction.text import TfidfVectorizer     # scikit-learn


def excepthook(type, value, tb):
    import traceback, pdb
    traceback.print_exception (type, value, tb)
    print
    pdb.pm ()


def parse_arguments():
    parser = argparse.ArgumentParser(description="Create a dynamic context (1bf - One Big File) by using the input parameter.")
    parser.add_argument("question", type=str, help="String pattern to be searched (regex)")
    parser.add_argument("pattern", type=str, help="String pattern to be searched (regex)")
    
    return parser.parse_args()


def extract_keywords(file_path, top_n=10):
    """
    Extract keywords from the file using TF-IDF.

    Args:
        file_path (str): Path to the file.
        top_n (int): Number of top keywords to extract.

    Returns:
        List[str]: List of top keywords.
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return []

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Preprocess content
    documents = [content]

    # Apply TF-IDF
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray()[0]

    # Get top keywords
    keyword_indices = scores.argsort()[-top_n:][::-1]
    keywords = [feature_names[i] for i in keyword_indices]

    return keywords


def main():
    sys.excepthook = excepthook

    print(">>>" + str(sys.argv))
    args = parse_arguments()

    # Access parsed arguments
    question = args.pattern   
    pattern = args.pattern  

    file_path = r"C:\Users\camicia\AppData\Local\Temp\dynamic_context\dynamic_context.1bf.txt"

    # Extract and print keywords
    keywords = extract_keywords(file_path)
    print("Top Keywords:", keywords)


if __name__ == "__main__":
    main()

# import pdb; pdb.set_trace()
