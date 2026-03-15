import json
import math
import os
import re
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer


config = None


def add_synonyms(words):
    
    additional_synonyms = load_additional_synonyms_file()

    if not config:
        config = load_json(config_file = os.path.join(os.path.dirname(__file__), "config.json"))

    synonyms = []
    words_lower = [word.lower() for word in words]
    for syns in config['synonyms_table'] + additional_synonyms:
        for s0 in syns:
            if s0 in words_lower:
                for s1 in syns:
                    if s1 not in words and s1 not in synonyms:
                        synonyms.append(s1)
    return(synonyms)


def get_most_relevant_words(words):
    """
    Remove stopwords, digits, short/long words, common words etc.
    """
    global config

    if not config:
        config = load_json(config_file = os.path.join(os.path.dirname(__file__), "config.json"))

    stop_words = set(stopwords.words('english'))
    words_temp = []
    for word in words:
        if len(word)>=2 \
            and len(word)<=32 \
            and not word.isdigit() \
            and word.lower() not in stop_words \
            and word.count('/') <= 1:

            words_temp.append(word)

    most_relevant_words = []
    common_words = []
    for word in words_temp:
        if word.lower() in config['common_words_to_ignore']:
            common_words.append(word)
        else:
            most_relevant_words.append(word)

    return(most_relevant_words, common_words)


def get_ngrams_freq(tokens, common_ngrams, common_ngrams_max_freq):
    tokens = [normalize(token).replace("_", " ") for token in tokens]
    tokens = " ".join(tokens)
    tokens = tokens.split()
    tokens = [token for token in tokens if len(token)>=2]

    ngrams_freq = defaultdict(int)
    for token1 in tokens:
        for token2 in tokens:
            if token1!=token2:
                for ngram, freq in common_ngrams.items():
                    if len(token1)>=3 and len(token2)>=3:
                        if re.search(f"{token1}.*{token2}", ngram):
                            ngrams_freq[f"{token1} {token2}"] += freq
                            # ngrams_freq[ngram] += freq
    return(ngrams_freq)


def get_ngrams_freq_strong(tokens, common_ngrams_strong, common_ngrams_strong_max_freq):
    tokens = [normalize(token).replace("_", " ") for token in tokens]
    tokens = " ".join(tokens)
    tokens = tokens.split()
    tokens = [token for token in tokens if len(token)>=2]

    global config
    if not config:
        config = load_json(config_file = os.path.join(os.path.dirname(__file__), "config.json"))
    
    ngrams_freq_strong = dict()
    for token1 in tokens:
        for token2 in tokens:
            if token1!=token2:
                ngram_list = [f"{token1} {token2}", ]
                for ngram_synonyms in config['ngram_synonyms_table']:
                    if ngram_list[0] in ngram_synonyms:
                        ngram_list = ngram_synonyms
                        break
                for ngram in ngram_list:
                    for common_ngram, freq in common_ngrams_strong.items():
                        if common_ngram == ngram:
                            ngrams_freq_strong[common_ngram] = freq

    return(ngrams_freq_strong)


def load_additional_synonyms_file():
    # Load the additional_synonyms.json file
    additional_synonyms_file = os.path.join(os.path.dirname(__file__), "..", "kb0", "additional_synonyms.json")
    with open(additional_synonyms_file, 'r', encoding='utf-8') as f:
        additional_synonyms = json.load(f)
    
    return (additional_synonyms)


def load_json(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


def normalize(keyword):
    norm_kw = keyword.lower()
    norm_kw = norm_kw.replace("/", "_")
    norm_kw = norm_kw.replace("-", "_")
    return(norm_kw)


def stemmer(tokens, already_there):
    already_there = tokens + already_there
    stemmer = PorterStemmer()
    stems = []
    for token in tokens:
        stem = stemmer.stem(token)
        if stem in ['confluenc', ]:
            continue
        if stem not in already_there and len(stem)>=2:
            stems.append(stem)
    return(stems)


def to_singular(tokens):
    lemmatizer = WordNetLemmatizer()
    singular_tokens = []
    for token in tokens:
        singular = lemmatizer.lemmatize(token, pos='n')
        if singular not in tokens and len(singular)>=2:
            singular_tokens.append(singular)
    return(singular_tokens)


def tokenize(text):
    """
    Tokenizes the input text into words, including those with slashes, dashes, and underscores.
    """
    tokens = re.findall(r'\b[\w/_-]+\b', text)
    return(tokens)


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


def get_patterns(question):
    # Pre-process the question
    pre_proc_question = question
    pre_proc_question = re.sub(r'\bpi\s+([0-9]{2}\.[0-9])\b', r'PI_\1', pre_proc_question, flags=re.IGNORECASE)
    # pre_proc_question = re.sub(r'[^a-zA-Z0-9\s/_-]', ' ', pre_proc_question)   # Remove non alpha-num

    # Tokenize
    tokens = tokenize(pre_proc_question)
    print(f"tokens : {tokens}")
    
    # Filter tokens - Remove stopwords, digits, short/long words, common words etc.
    (most_relevant_words, common_words) = get_most_relevant_words(tokens)
    print(f"most_relevant_words : {most_relevant_words}")
    print(f"common_words : {common_words}")
    
    # To singular
    singular_tokens = to_singular(most_relevant_words)
    print(f"singular_tokens : {singular_tokens}")

    # Stemmer
    stems = stemmer(most_relevant_words, singular_tokens)
    print(f"stems : {stems}")

    # Synonyms
    synonyms = add_synonyms(most_relevant_words + singular_tokens + stems)
    print(f"synonyms : {synonyms}")

    all_tokens = sorted(set(most_relevant_words + synonyms + singular_tokens + stems))

    # Load keywords files
    (keywords, keywords_max_freq, 
     ngrams_global, ngrams_max_freq,
     ngrams_strong_global, ngrams_strong_max_freq,
     normalized_words, normalized_words_max_freq) = load_keywords_files()

    # Search for common ngrams
    ngrams_freq = get_ngrams_freq(all_tokens, ngrams_global, ngrams_max_freq)

    # Search for common ngrams (strong match)
    ngrams_freq_strong = get_ngrams_freq_strong(all_tokens, ngrams_strong_global, ngrams_strong_max_freq)
    
    # Other synonyms
    other_synonymms = add_synonyms(ngrams_freq_strong)
    
    patterns = defaultdict(dict)
    
    # Words
    for token in all_tokens:
        freq = keywords.get(token, None)
        if freq:
            patterns["words"][token] = math.log(freq/keywords_max_freq)
    
    # normalized_words
    for token in all_tokens:
        normalized_token = normalize(token)
        if normalized_token in normalized_words:
            freq = normalized_words[normalized_token]['frequency']
            # freq_str = f"{math.log(freq/normalized_words_max_freq):.1f}" if freq else None
            # variants = normalized_words[normalized_token]['variants']
            # most_common = max(variants, key=variants.get)
            # most_common = most_common[0] + most_common[1:-1].replace("o", "O") + most_common[-1]  # SoC -> SOC
            # acronym = (most_common.upper()==most_common)
            # acronym_str = f' (acronym:{max(variants, key=variants.get)})' if acronym else ''
            patterns["normalized_words"][normalized_token] = math.log(freq/normalized_words_max_freq)

    # ngrams : non-exact occurrences in ngrams
    for ngram, freq in ngrams_freq.items():
        patterns["ngrams"][ngram] = math.log(freq/ngrams_max_freq)
        
    # other_synonymms - second stage of synyms search
    for word in other_synonymms:
        patterns["other_synonymms"][word] = 0

    # ngrams-and-terms : occurrences both present in ngrams and normalized_words
    for ngram, freq in ngrams_freq.items():
        if ngram.replace(" ", "_") in normalized_words:
            patterns["ngrams-and-terms"][ngram] = math.log(freq/ngrams_max_freq)

    # ngrams_strong : exact occurrences in ngrams_strong
    for ngram, freq in ngrams_freq_strong.items():
        patterns["ngrams_strong"][ngram] = math.log(freq/ngrams_max_freq)
    
    # Print the patterns
    
    single_search = []

    print("\nwords ('-_/' -> '.?'):")
    for pattern, freq in sorted(patterns["words"].items(), key=lambda item: item[1], reverse=True):
        freq_str = f"{freq:.1f}" if freq else None
        print(f"    {pattern} : {freq_str}")
        ptrn = re.sub(r'[-_/]', '.?', pattern)
        if ptrn not in single_search:
            single_search.append(ptrn)

    print("\nnormalized_words ('_' -> '.'):")
    for pattern, freq in sorted(patterns["normalized_words"].items(), key=lambda item: item[1], reverse=True):
        freq_str = f"{freq:.1f}" if freq else None
        print(f"    {pattern} : {freq_str}")
        ptrn = pattern.replace('_', '.')
        if ptrn not in single_search:
            single_search.append(ptrn)

    # ngrams_strong
    print("\nngrams_strong - exact occurrences in ngrams_strong (' ' -> ' '):")
    for pattern, freq in sorted(patterns["ngrams_strong"].items(), key=lambda item: item[1], reverse=True):
        freq_str = f"{freq:.1f}" if freq else None
        print(f"    {pattern} : {freq_str}")
        if pattern not in single_search:
            single_search.append(pattern)
            
    print("\nngrams-and-terms - occurrences both present in ngrams and normalized_words (' ' -> '.?'):")
    for pattern, freq in sorted(patterns["ngrams-and-terms"].items(), key=lambda item: item[1], reverse=True):
        freq_str = f"{freq:.1f}" if freq else None
        print(f"    {pattern} : {freq_str}")
        ptrn = pattern.replace(' ', '.?')
        if ptrn not in single_search:
            single_search.append(ptrn)

    print("\nother_synonymms - second stage of synyms search (' _' -> '.?'):")
    for pattern, freq in sorted(patterns["other_synonymms"].items(), key=lambda item: item[1], reverse=True):
        freq_str = f"{freq:.1f}" if freq else None
        print(f"    {pattern} : {freq_str}")
        ptrn = re.sub(r'[ _]', '.?', pattern)
        if ptrn not in single_search:
            single_search.append(ptrn)

    print("\nNgrams - non-exact occurrences in ngrams (' ' -> '.*'):")
    for pattern, freq in sorted(patterns["ngrams"].items(), key=lambda item: item[1], reverse=True):
        freq_str = f"{freq:.1f}" if freq else None
        print(f"    {pattern} : {freq_str}")       
        ptrn = pattern.replace(' ', '.*')
        if ptrn not in single_search:
            single_search.append(ptrn)

    # single_search_whole_word = []
    # single_search_multiple_words = []
    # for pattern in single_search:
    #     if any(char in pattern for char in ' ._-?/'):
    #         single_search_multiple_words.append(pattern)
    #     else:
    #         single_search_whole_word.append(pattern)

    print("\nSingle search patterns:")
    for pattern in single_search:
        print(f"    {pattern}")       

    print("\nRegex:")
    regex = "|".join(single_search)
    print(f"    {regex}")
    
    # print("\nPatterns")
    # if 'ngrams' in patterns:
    #     ngrams = patterns['ngrams']
    #     pattern = max(ngrams, key=ngrams.get)
    #     print(f"    {pattern}")
    
    return(tokens)

# import pdb; pdb.set_trace()
