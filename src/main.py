#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from collections import Counter
from math import inf
from copy import copy
import random
from collections import defaultdict, Counter

from music21.converter import Converter, parse

from vector_helpers import streamToIntervals, intervalToVector, buildCorpus, parseMeasures, docToVector

# import ranking classes
from lib.midi_levenshtein_lcs.modules.composition_lcs_score import LCS
from lib.midi_levenshtein_lcs.modules.composition_levenshtein_score import Levenshtein
from lib.midi_levenshtein_lcs.lib.helpers import Music21Helper
from lib.music_ranker.music_ranker import MusicRanker

# import logic to parse the case dataset
from lib.preprocess.parse_cases import parseData, buildFileList

from constants import DATA_DIR, CASES_XML

# either posix path or pycache was causing a weird issue
# where works in each case were being interpretted as identical
# by music21.converter.parse
# Only solution I could come to that worked was to unzip all the
# data to pure xml or midi files and move them to a new directory
# which I called data_clean. At that point I was able to get results as expected.

helper = Music21Helper()

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

# build a vector corpus
vector_corpus = buildCorpus(cases, vectors=True, vector_min=vector_min, vector_max=vector_max)

# build the 'vertical' corpus
vertical_corpus = buildCorpus(cases, vertical=True)

# build the melody (interval) corpus so we can account for doc length
interval_corpus = buildCorpus(cases)

# at this point we have words, but we want to get vectors of c(w,d)
# get a vocab so we know how to build each vector (one slot per word in the vocab)
vocab = Counter()
for doc in vertical_corpus:
    vocab += Counter(doc)

# declare a new var for the vectorized corpus
vertical_corpus_vectors = []
# for each work
for doc in vertical_corpus:
    vector = []
    # for each word in the vocab
    doc = Counter(doc)
    for word in vocab:
        vector.append(doc[word])
    vertical_corpus_vectors.append(vector)


# run some experiments
NUM_ITERATIONS = 10

final_results_horizontal = defaultdict(list)
final_results_vertical = defaultdict(list)

for i in range(NUM_ITERATIONS):

    scores = []
    results = defaultdict(defaultdict)
    lcs_correct = 0
    lev_correct = 0
    bm25_correct = 0
    pln_correct = 0
    # driver code for "horizontal" analysis
    # convert music into vectors, pretty straight forward setup

    # instantiate a 'document ranker'
    ranker = MusicRanker(vector_corpus, b=0.75, k=1.2, reference_corpus=interval_corpus)


    keys = list(cases.keys())

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

        # get the list of keys minus the current key
        valid_keys = copy(keys)
        valid_keys.remove(key)
        # select an unrelated cases
        random_case = random.choice(valid_keys)
        # choose from comp or def
        random_cd = random.choice(["complaintant", "defendant"])
        # get the work and its melody
        random_work = cases[random_case][random_cd]
        random_file = random_work["file"]
        random_work = parse(DATA_DIR + "/" + random_file)
        random_melody = streamToIntervals(random_work)


        # compute string matching similarities
        lcs_score = helper.lcsDP(c_melody, d_melody)
        lev_score = helper.levenshteinDistanceDP(c_melody, d_melody)
        lcs_score_base = helper.lcsDP(c_melody, random_melody)
        lev_score_base = helper.levenshteinDistanceDP(c_melody, random_melody)
        # scores.append((lcs_score, lev_score))

        # string matching results
        results[key]["LCS"] = True if lcs_score > lcs_score_base else False
        lcs_correct += 1 if lcs_score > lcs_score_base else 0
        results[key]["Levenshtein"] = True if lev_score > lev_score_base else False
        lev_correct += 1 if lev_score > lev_score_base else 0

        # convert the interval list to a vector
        c_vector = intervalToVector(c_melody, vector_min, vector_max)
        d_vector = intervalToVector(d_melody, vector_min, vector_max)
        random_vector = intervalToVector(random_melody, vector_min, vector_max)

        # at this point we can use dot product, bm25, and pivoted length normalization with the vector representation
        # will need to do a little more processing to use probabilistic models like JM smoothing and Dirichlet smoothing
        
        # text mining similarities
        bm25_score = ranker.bm25(d_vector, c_vector)
        bm25_score_base = ranker.bm25(random_vector, c_vector)
        pln_score = ranker.pivoted_length_normalization(d_vector, c_vector)
        pln_score_base = ranker.pivoted_length_normalization(random_vector, c_vector)

        # text mining results
        results[key]["BM25"] = True if bm25_score > bm25_score_base else False
        bm25_correct += 1 if bm25_score > bm25_score_base else 0
        results[key]["PLN"] = True if pln_score > pln_score_base else False
        pln_correct += 1 if pln_score > pln_score_base else 0

    horizontal_statistics = defaultdict(defaultdict)
    horizontal_statistics["BM25"]["correct"] = bm25_correct / cases.__len__()
    horizontal_statistics["PLN"]["correct"] = pln_correct / cases.__len__()
    horizontal_statistics["LCS"]["correct"] = lcs_correct / cases.__len__()
    horizontal_statistics["Levenshtein"]["correct"] = lev_correct / cases.__len__()

    print("==========================")
    print("Horizontal results")
    print("==========================")
    print(horizontal_statistics)
    print("==========================")
    print("==========================")

    final_results_horizontal["LCS"].append(horizontal_statistics["LCS"]["correct"])
    final_results_horizontal["Lev"].append(horizontal_statistics["Levenshtein"]["correct"])
    final_results_horizontal["BM25"].append(horizontal_statistics["BM25"]["correct"])
    final_results_horizontal["PLN"].append(horizontal_statistics["PLN"]["correct"])

    # driver code for "vertical" analysis
    # analyze groups of notes together. we will consider
    # the group of notes that occur in a measure to be a "word."
    # best approach is probably to get the notes, sort them, and
    # represent as intervals. not sure how to standardize.


    # instantiate a 'document ranker' with the original corpus as a reference
    ranker = MusicRanker(vertical_corpus_vectors, b=0.75, k=1.2, reference_corpus=vertical_corpus)

    scores = []
    results = defaultdict(defaultdict)
    lcs_correct = 0
    lev_correct = 0
    bm25_correct = 0
    pln_correct = 0

    for key, case in cases.items():
        # get the file name and type or the defendant and complaintant
        c_file = case["complaintant"]["file"]
        c_type = case["complaintant"]["fileType"]
        d_file = case["defendant"]["file"]
        d_type = case["defendant"]["fileType"]
        
        complaintant = parse(DATA_DIR + "/" + c_file)
        defendant = parse(DATA_DIR + "/" + d_file)

        # parse the works into measure words
        c_words = parseMeasures(complaintant)
        d_words = parseMeasures(defendant)

        # get the list of keys minus the current key
        valid_keys = copy(keys)
        valid_keys.remove(key)
        # select an unrelated cases
        random_case = random.choice(valid_keys)
        # choose from comp or def
        random_cd = random.choice(["complaintant", "defendant"])
        # get the work and its melody
        random_work = cases[random_case][random_cd]
        random_file = random_work["file"]
        random_work = parse(DATA_DIR + "/" + random_file)
        random_words = parseMeasures(random_work)

        # score by string matching techniques
        lcs_score = helper.lcsDP(c_words, d_words)
        lev_score = helper.levenshteinDistanceDP(c_words, d_words)
        lcs_score_base = helper.lcsDP(c_words, random_words)
        lev_score_base = helper.levenshteinDistanceDP(c_words, random_words)

        # get each work as a vector
        c_vector = docToVector(c_words, vocab)
        d_vector = docToVector(d_words, vocab)
        random_vector = docToVector(random_words, vocab)

        # vector text mining scores
        bm25_score = ranker.bm25(d_vector, c_vector)
        pln_score = ranker.pivoted_length_normalization(d_vector, c_vector)
        bm25_score_base = ranker.bm25(c_vector, random_vector)
        pln_score_base = ranker.pivoted_length_normalization(c_vector, random_vector)

        # string matching results
        results[key]["LCS"] = True if lcs_score > lcs_score_base else False
        lcs_correct += 1 if lcs_score > lcs_score_base else 0
        results[key]["Levenshtein"] = True if lev_score > lev_score_base else False
        lev_correct += 1 if lev_score > lev_score_base else 0

        # text mining results
        results[key]["BM25"] = True if bm25_score > bm25_score_base else False
        bm25_correct += 1 if bm25_score > bm25_score_base else 0
        results[key]["PLN"] = True if pln_score > pln_score_base else False
        pln_correct += 1 if pln_score > pln_score_base else 0

        # scores.append((c_words, d_words))


    vertical_statistics = defaultdict(defaultdict)
    vertical_statistics["BM25"]["correct"] = bm25_correct / cases.__len__()
    vertical_statistics["PLN"]["correct"] = pln_correct / cases.__len__()
    vertical_statistics["LCS"]["correct"] = lcs_correct / cases.__len__()
    vertical_statistics["Levenshtein"]["correct"] = lev_correct / cases.__len__()

    print("Vertical results")
    print("==========================")
    print(vertical_statistics)
    print("==========================")
    print("==========================")

    final_results_vertical["LCS"].append(vertical_statistics["LCS"]["correct"])
    final_results_vertical["Lev"].append(vertical_statistics["Levenshtein"]["correct"])
    final_results_vertical["BM25"].append(vertical_statistics["BM25"]["correct"])
    final_results_vertical["PLN"].append(vertical_statistics["PLN"]["correct"])

print("=================")
print("=================")
print("=================")
print("=================")
print("horizontal final results:")
print("LCS max: {}".format(max(final_results_horizontal["LCS"])))
print("LCS min: {}".format(min(final_results_horizontal["LCS"])))
print("LCS avg: {}".format(sum(final_results_horizontal["LCS"])/len(final_results_horizontal["LCS"])))
print("\n")
print("Lev max: {}".format(max(final_results_horizontal["Lev"])))
print("Lev min: {}".format(min(final_results_horizontal["Lev"])))
print("Lev avg: {}".format(sum(final_results_horizontal["Lev"])/len(final_results_horizontal["Lev"])))
print("\n")
print("BM25 max: {}".format(max(final_results_horizontal["BM25"])))
print("BM25 min: {}".format(min(final_results_horizontal["BM25"])))
print("BM25 avg: {}".format(sum(final_results_horizontal["BM25"])/len(final_results_horizontal["BM25"])))
print("\n")
print("PLN max: {}".format(max(final_results_horizontal["PLN"])))
print("PLN min: {}".format(min(final_results_horizontal["PLN"])))
print("PLN avg: {}".format(sum(final_results_horizontal["PLN"])/len(final_results_horizontal["PLN"])))
print("\n")

print("=================")
print("=================")
print("vertical final results:")
print("LCS max: {}".format(max(final_results_vertical["LCS"])))
print("LCS min: {}".format(min(final_results_vertical["LCS"])))
print("LCS avg: {}".format(sum(final_results_vertical["LCS"])/len(final_results_vertical["LCS"])))
print("\n")
print("Lev max: {}".format(max(final_results_vertical["Lev"])))
print("Lev min: {}".format(min(final_results_vertical["Lev"])))
print("Lev avg: {}".format(sum(final_results_vertical["Lev"])/len(final_results_vertical["Lev"])))
print("\n")
print("BM25 max: {}".format(max(final_results_vertical["BM25"])))
print("BM25 min: {}".format(min(final_results_vertical["BM25"])))
print("BM25 avg: {}".format(sum(final_results_vertical["BM25"])/len(final_results_vertical["BM25"])))
print("\n")
print("PLN max: {}".format(max(final_results_vertical["PLN"])))
print("PLN min: {}".format(min(final_results_vertical["PLN"])))
print("PLN avg: {}".format(sum(final_results_vertical["PLN"])/len(final_results_vertical["PLN"])))
print("\n")
