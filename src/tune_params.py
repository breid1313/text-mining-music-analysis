import os
from pathlib import Path
from collections import Counter
from math import inf

from music21.converter import Converter, parse

# import ranking classes
from lib.midi_levenshtein_lcs.modules.composition_lcs_score import LCS
from lib.midi_levenshtein_lcs.modules.composition_levenshtein_score import Levenshtein
from lib.midi_levenshtein_lcs.lib.helpers import Music21Helper
from lib.document_ranker.algorithms.document_ranker import Ranker
from lib.music_ranker.music_ranker import MusicRanker

# import logic to parse the case dataset
from lib.preprocess.parse_cases import parseData, buildFileList

# import helpers from the main file
from vector_helpers import streamToIntervals, intervalToVector, buildCorpus

from constants import DATA_DIR, CASES_XML

# either posix path or pycache was causing a weird issue
# where works in each case were being interpretted as identical
# by music21.converter.parse
# Only solution I could come to that worked was to unzip all the
# data to pure xml or midi files and move them to a new directory
# which I called data_clean. At that point I was able to get results as expected.

# build the dict of case pairings
cases = parseData(CASES_XML)
# build the dict of songs without pairing by case
all_songs = buildFileList(CASES_XML)

# optimize the size of the vectors
# vector_min, vector_max = getMaxIntervals(cases)
# returns -18,14
# will use -20,20 for now, static to save time
vector_min = -20
vector_max = 20

scores = []

b_values = [i/100 for i in range(101)] # 0 to 1
k_values = [i/100 for i in range(301)] # 0 to 3

# driver code for "horizontal" analysis
# convert music into vectors, pretty straight forward setup
for key, case in cases.items():
    # get the file name and type or the defendant and complaintant
    c_file = case["complaintant"]["file"]
    c_type = case["complaintant"]["fileType"]
    d_file = case["defendant"]["file"]
    d_type = case["defendant"]["fileType"]

    # get the complaintant as a list of intervals
    complaintant = parse(DATA_DIR + "/" + c_file)
    c_melody = streamToIntervals(complaintant)

    # get the defendant as a list of intervals
    defendant = parse(DATA_DIR + "/" + d_file)
    d_melody = streamToIntervals(defendant)

    # convert the interval list to a vector
    c_vector = intervalToVector(c_melody, vector_min, vector_max)
    d_vector = intervalToVector(d_melody, vector_min, vector_max)

    corpus = buildCorpus(cases, vectors=True, vector_min=vector_min, vector_max=vector_max)

    # bm25

    best_b = None
    max_score = -inf
    for b in b_values:
        print("testing b = {}".format(b))
        ranker = MusicRanker(corpus=corpus, b=b, k=1.2)
        score = ranker.bm25(d_vector, c_vector)
        if score >= max_score:
            max_score = score
            best_b = b
    print("Optimal B value: {}".format(b))


    # PLN

    best_b = None
    max_score = -inf
    for b in b_values:
        print("testing b = {}".format(b))
        ranker = MusicRanker(corpus=corpus, b=b, k=1.2)
        score = ranker.pivoted_length_normalization(d_vector, c_vector)
        if score >= max_score:
            max_score = score
            best_b = b
    print("Optimal B value: {}".format(b))

    best_k = None
    max_score = -inf
    for k in k_values:
        print("testing k = {}".format(k))
        ranker = MusicRanker(corpus, b=0.75, k=k)
        score  = ranker.pivoted_length_normalization(d_vector, c_vector)
        if score >= max_score:
            max_score = score
            best_k = k
    print("Optimal k value: {}".format(k))

