# Script: keywords.py
# Description: Analyze a knowledge base to extract and rank keywords.
#
# Usage: 
#
# Parameters:
#   
#
# Examples:
#   python keywords.py

import glob
import json
import math
import nltk
import os
import re
import sys
from collections import Counter
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


common_words_to_ignore = ['shall', 'none', 'document', 'documentation', 'describe', 'described', 'describes']


def excepthook(type, value, tb):
    import traceback, pdb
    traceback.print_exception (type, value, tb)
    print
    pdb.pm ()


def filter_tokens(tokens):
    """
    Remove stopwords, digits, too short/long words, too common words etc.
    """
    stop_words = set(stopwords.words('english'))
    filtered_tokens = []
    for word in tokens:
        if len(word)>=2 \
            and len(word)<=32 \
            and not word.isdigit() \
            and word.lower() not in stop_words \
            and word.lower() not in common_words_to_ignore \
            and word.count('/') <= 1:

            filtered_tokens.append(word)
    return(filtered_tokens)
    
    
def get_ngrams(tokens):
    """
    Extracts bigrams and trigrams from the list of tokens, ignoring common words.
    Returns a dictionary of n-grams with their frequencies, sorted by frequency and truncated to the top 20%.
    """
    ngrams = defaultdict(int)
    for i, token in enumerate(tokens):
        if (i+2)>=len(tokens):
            break
        norm_kw_1 = normalize(token)
        norm_kw_2 = normalize(tokens[i+1])
        norm_kw_3 = normalize(tokens[i+2])

        ngram = (norm_kw_1 + " " + norm_kw_2).replace("_", " ").strip()
        ngram = re.sub(r'\s+', ' ', ngram)
        ngrams[ngram] += 1

        ngram = (norm_kw_1 + " " + norm_kw_2 + " " + norm_kw_3).replace("_", " ").strip()
        ngram = re.sub(r'\s+', ' ', ngram)
        ngrams[ngram] += 1
            
    sorted_ngrams = dict(sorted(ngrams.items(), key=lambda x: (-x[1], x[0])))

    sorted_ngrams_truncated_length = int(0.2 * len(sorted_ngrams))

    sorted_ngrams = dict(list(sorted_ngrams.items())[:sorted_ngrams_truncated_length])
    
    # todo: items are sorted => the truncation provileges the first alpha characters => items with the same freq must be shuffled by using a hash.
    
    return(sorted_ngrams)


def get_singular(word_frequencies):
    """
    Converts plural nouns to their singular forms and aggregates their frequencies.
    """
    
    lemmatizer = WordNetLemmatizer()
    singular_word_frequencies = Counter()
    
    for word, count in word_frequencies.items():
        singular_word = lemmatizer.lemmatize(word, pos='n')
        singular_word_frequencies[singular_word] += count

    # Sort by frequency (descending), then alphabetically
    singular_word_frequencies = dict(sorted(singular_word_frequencies.items(), key=lambda x: (-x[1], x[0])))
    
    return singular_word_frequencies


def get_word_frequencies(words):
    """
    Count the frequency of each word.
    """
    word_frequencies = {}
    for word in words:
        word_frequencies[word] = word_frequencies.get(word, 0) + 1

    return word_frequencies


def get_files(path):
    files = glob.glob(os.path.join(path, "**", "*.txt"), recursive=True)
    md_files = glob.glob(os.path.join(path, "**", "*.md"), recursive=True)
    files.extend(md_files)
    return(files)


def extract_words_from_files(files):
    """
    Returns the sequence of words from the knowledge base files.
    Returns:
    words_sequence : sequence of words as is.
    """

    combined_content = ""
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            combined_content += file.read() + "\n"

    combined_content = combined_content.replace("https://", "")
    combined_content = combined_content.replace(".tttech.com", "")
            
    print(f"\nExtracting words from {len(files)} files. Total size: {len(combined_content) / 1024 / 1024:.1f} MB")

    # Tokenize
    words_sequence = tokenize(combined_content)
    
    return(words_sequence)


def group_by_normalized_form(keywords):
    """
    Groups keywords by their normalized forms (lowercase with dashes/slashes converted to underscores) 
    and aggregates their frequencies while tracking all original variants.
    """

    # Example:
    # "client_server": {
    #     "frequency": 375,
    #     "variants": {
    #         "Client/Server": 53,
    #         "client/server": 280,
    #         "Client-Server": 5,
    #         "Client/server": 25,
    #         "Client-server": 4,
    #         "client-server": 8
    #     }
    # },

    normalized_words = defaultdict(dict)
    for keyword, frequency in keywords.items():
        norm_kw = normalize(keyword)

        if 'frequency' not in normalized_words[norm_kw]:
            normalized_words[norm_kw]['frequency'] = 0
            normalized_words[norm_kw]['variants'] = dict()
        normalized_words[norm_kw]['variants'][keyword] = frequency
        normalized_words[norm_kw]['frequency'] += frequency

    return(normalized_words) 


def normalize(word):
    """
    Converts a word to lowercase and replaces dashes and slashes with underscores for consistent normalization.
    """
    norm_kw = word.lower()
    norm_kw = norm_kw.replace("/", "_")
    norm_kw = norm_kw.replace("-", "_")
    return(norm_kw)


def tokenize(text):
    """
    Tokenizes the input text into words, including those with slashes, dashes, and underscores.
    """
    tokens = re.findall(r'\b[\w/_-]+\b', text)
    return(tokens)
    
    
def kb_analyze(files):
    """
    Analyze the knowledge base.
    Returns:
    words : dictionary of words with their frequencies. Words are converted to their singular forms.
    normalized_words : dictionary of normalized words with their frequencies and variants. 'Normalized' means  lowercase with dashes/slashes converted to underscores.
    ngrams : n-grams (bigrams and trigrams) with their frequencies from filtered words sequence.
    ngrams_strong : n-grams from words sequence as is.
    """
    
    words_sequence = extract_words_from_files(files)
    filtered_words_sequence = filter_tokens(words_sequence)             # Remove stopwords, digits, too short/long words, too common words etc.
    word_frequencies = get_word_frequencies(filtered_words_sequence)    # Count the frequency of each word.
    normalized_words = group_by_normalized_form(word_frequencies)
    ngrams = get_ngrams(filtered_words_sequence)        # Get ngrams from filtered words sequence
    ngrams_strong = get_ngrams(words_sequence)          # Get ngrams from words sequence as is
    words = get_singular(word_frequencies)
    
    return(words, normalized_words, ngrams, ngrams_strong)


def main():
    sys.excepthook = excepthook

    path = r"C:\Dev_Analisys\kb0"
    
    files = get_files(path)
    
    # Analyze the knowledge base.
    (words, normalized_words, ngrams, ngrams_strong) = kb_analyze(files)

    print(f"Found {len(words)} words")

    # Create words.json : dictionary of words with their frequencies. Words are converted to their singular forms.
    output_file = os.path.join(path, "words.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(words, f, ensure_ascii=False, indent=4)
    print(f"File created: {output_file}")

    # Create normalized_words.json : dictionary of normalized words with their frequencies and variants. 
    # 'Normalized' means  lowercase with dashes/slashes converted to underscores.
    output_file = os.path.join(path, "normalized_words.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(normalized_words, f, ensure_ascii=False, indent=4)
    print(f"File created: {output_file}")

    # Create ngrams.json : n-grams (bigrams and trigrams) with their frequencies from filtered words sequence.
    output_file = os.path.join(path, "ngrams.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ngrams, f, ensure_ascii=False, indent=4)
    print(f"File created: {output_file}")

    # Create ngrams_strong.json : n-grams from words sequence as is.
    output_file = os.path.join(path, "ngrams_strong.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(ngrams_strong, f, ensure_ascii=False, indent=4)
    print(f"File created: {output_file}")


if __name__ == "__main__":
    main()

# import pdb; pdb.set_trace()
