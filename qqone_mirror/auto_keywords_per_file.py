# Script: auto_keywords_per_file.py
# Description: This script returns the most relevant keywords for each file.
#
# Usage: 
#
# Parameters:
#
# Examples:
#   python auto_keywords_per_file.py

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


# Load configuration from JSON file
def load_config(kb_name):

    config_file = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON syntax in configuration file: {config_file}")
        print(f"  Line {e.lineno}, Column {e.colno}: {e.msg}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load configuration file: {config_file}")
        print(f"  {type(e).__name__}: {e}")
        sys.exit(1)

    assert('kb_configs' in config)
    kb_configs = config['kb_configs']
    assert(kb_name in kb_configs)
    kb_config_path = kb_configs[kb_name]
    try:
        with open(kb_config_path, 'r', encoding='utf-8') as f:
            kb_config = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {kb_config_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON syntax in configuration file: {kb_config_path}")
        print(f"  Line {e.lineno}, Column {e.colno}: {e.msg}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to load configuration file: {kb_config_path}")
        print(f"  {type(e).__name__}: {e}")
        sys.exit(1)
    config['kb_config'] = kb_config

    return config


config = load_config('kb0')
COMMON_WORDS_TO_IGNORE = config['common_words_to_ignore']
SYNONYMS_TABLE = config['synonyms_table']
NGRAM_SYNONYMS_TABLE = config['ngram_synonyms_table']


def excepthook(type, value, tb):
    import traceback, pdb
    traceback.print_exception (type, value, tb)
    print
    pdb.pm ()

    
def auto_keywords_per_file(files):

    # Load keywords files
    (keywords, keywords_max_freq, 
     ngrams_global, ngrams_max_freq,
     ngrams_strong_global, ngrams_strong_max_freq,
     normalized_words, normalized_words_max_freq) = load_keywords_files()
    
    total_words_global = 0
    for data in normalized_words.values():
        total_words_global += data['frequency']

    for file_path in files:
        words_sequence_current = extract_words_from_files(files)
        filtered_words_sequence_current = filter_tokens(words_sequence_current)             # Remove stopwords, digits, too short/long words, too common words etc.
        word_frequencies_current = get_word_frequencies(filtered_words_sequence_current)    # Count the frequency of each word.
        normalized_words_current = group_by_normalized_form(word_frequencies_current)
    
        total_words_current = 0
        for data_current in normalized_words_current.values():
            total_words_current += data_current['frequency']

        print(f"File: {file_path}")

        words_list = []
        words_freq_current = []
        for word_current, data_current in normalized_words_current.items():
            freq_current = data_current['frequency']
            freq_global = normalized_words[word_current]['frequency']
            
            freq_rel_global = freq_global/total_words_global
            freq_rel_current = freq_current/total_words_current
            
            specificity = freq_rel_current/freq_rel_global
            
            if specificity>1 and len(word_current)>=3 and freq_current>=4:
                words_list.append((word_current, specificity, freq_current))
        
        # Sort words by specificity (descending)
        words_list.sort(key=lambda x: x[1], reverse=True)
        words_list = [(word, specific, freq_current, specific_index) for specific_index, (word, specific, freq_current) in enumerate(words_list)]
        words_list.sort(key=lambda x: x[2], reverse=True)
        words_list = [(word, specific, freq_current, specific_index, freq_current_index) for freq_current_index, (word, specific, freq_current, specific_index) in enumerate(words_list)]

        words_list = [(word, specific, freq_current, specific_index, freq_current_index, specific_index+freq_current_index) for freq_current_index, (word, specific, freq_current, specific_index, freq_current_index) in enumerate(words_list)]
        words_list.sort(key=lambda x: x[5])

        print(words_list[:4])


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
            and word.lower() not in COMMON_WORDS_TO_IGNORE \
            and word.count('/') <= 1:

            filtered_tokens.append(word)
    return(filtered_tokens)


def get_files(path):
    files = glob.glob(os.path.join(path, "**", "*.txt"), recursive=True)
    md_files = glob.glob(os.path.join(path, "**", "*.md"), recursive=True)
    files.extend(md_files)
    return(files)


def get_word_frequencies(words):
    """
    Count the frequency of each word.
    """
    word_frequencies = {}
    for word in words:
        word_frequencies[word] = word_frequencies.get(word, 0) + 1

    return word_frequencies


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


def load_keywords_files():
    """
    Load all JSON data files and return the data with max frequencies.
    """
    # Load the words.json file
    keywords_file = os.path.join(os.path.dirname(__file__), "..", "kb0", "words.json")
    with open(keywords_file, 'r', encoding='utf-8') as f:
        keywords = json.load(f)     # Such words are lower case and singular
    keywords_max_freq = next(iter(keywords.items()))[1]

    # Load the ngrams.json file
    ngrams_file = os.path.join(os.path.dirname(__file__), "..", "kb0", "ngrams.json")
    with open(ngrams_file, 'r', encoding='utf-8') as f:
        ngrams = json.load(f)     # Such words are lower case and singular
    ngrams_max_freq = next(iter(ngrams.items()))[1]

    # Load the ngrams_strong.json file
    ngrams_strong_file = os.path.join(os.path.dirname(__file__), "..", "kb0", "ngrams_strong.json")
    with open(ngrams_strong_file, 'r', encoding='utf-8') as f:
        ngrams_strong = json.load(f)     # Such words are lower case and singular
    ngrams_strong_max_freq = next(iter(ngrams_strong.items()))[1]

    # Load the normalized_words.json file
    normalized_words_file = os.path.join(os.path.dirname(__file__), "..", "kb0", "normalized_words.json")
    with open(normalized_words_file, 'r', encoding='utf-8') as f:
        normalized_words = json.load(f)     # Such words are lower case and singular
    normalized_words_max_freq = next(iter(normalized_words.items()))[1]['frequency']
    
    return (keywords, keywords_max_freq, 
            ngrams, ngrams_max_freq, 
            ngrams_strong, ngrams_strong_max_freq, 
            normalized_words, normalized_words_max_freq)


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


def main():
    sys.excepthook = excepthook

    # path = r"C:\Dev_Analisys\kb0"
    path = r"C:\Dev_Analisys\kb0\exports_auto\general_confluence"
    
    files = get_files(path)
    
    # files = [r"C:\Dev_Analisys\kb0\imports\jira\SPTDEFECT_5610_COM_RTE_ISSM_Missing_reference_to_QNX.txt", ]
        
    auto_keywords_per_file(files)


if __name__ == "__main__":
    main()

# import pdb; pdb.set_trace()
