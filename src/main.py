#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

# import logic to parse the case dataset
from lib.preprocess.parse_cases import parseData

# either posix path or pycache was causing a weird issue
# where works in each case were being interpretted as identical
# by music21.converter.parse
# Only solution I could come to that worked was to unzip all the
# data to pure xml or midi files and move them to a new directory
# which I called data_clean. At that point I was able to get results as expected.
DATA_DIR = os.path.abspath("./data_clean")
CASES_XML = Path(__file__).parent.parent / "data/dataset.xml"

def streamToIntervals(stream):
    """Takes a music21 stream, isolates the first part (melody)
    and returns it as a vector of intervals.

    :param stream: music21 stream/score
    :type stream: music21.Stream
    """
    melody = stream.parts[0]
    melody = melody.pitches
    melody = [pitch.diatonicNoteNum for pitch in melody]
    melody = [melody[i+1] - melody[i] for i in range(len(melody)-1)]
    return melody

def intervalToVector(intervalList, start=-30, end=30):
    """Takes a list of intervals ie [0,2,-3,...] and converts
    it to a vector via the Counter object.

    :param intervalList: lift of ints representing diatonic intervals
    :type intervalList: list
    :return: vector of interval frequency
    :rtype: list
    """
    counter = Counter()
    for interval in intervalList:
        counter[interval] += 1
    result = [counter[i] for i in range(start,end+1)]
    return result

def getMaxIntervals(cases):
    """takes a cases dictionary, reads each of the files in question,
    and determines the min an max intervals present in the dataset. This
    information is used to optimize the size of the vectors we use to
    store the music.

    :param cases: case information
    :type cases: dict
    """
    min_interval = inf
    max_interval = -inf

    for key, case in cases.items():
        # get the file name and type or the defendant and complaintant
        c_file = case["complaintant"]["file"]
        c_type = case["complaintant"]["fileType"]
        d_file = case["defendant"]["file"]
        d_type = case["defendant"]["fileType"]

        # get the complaintant as a list of intervals
        complaintant = parse(DATA_DIR + "/" + c_file)
        c_melody = streamToIntervals(complaintant)
        # update the min and max values if necessary
        local_max = max(c_melody)
        if local_max >= max_interval:
            max_interval = local_max
        local_min = min(c_melody)
        if local_min <= min_interval:
            min_interval = local_min

        # get the defendant as a list of intervals
        defendant = parse(DATA_DIR + "/" + d_file)
        d_melody = streamToIntervals(defendant)
        # update the min and max values if necessary
        local_max = max(d_melody)
        if local_max >= max_interval:
            max_interval = local_max
        local_min = min(d_melody)
        if local_min <= min_interval:
            min_interval = local_min

    return min_interval, max_interval

def buildCorpus(cases, vertical=False):
    """Iterates over each case to parse the data into interval notation,
    adding each work to a list so that we can build a corpus.

    :param cases: cases dictionary
    :type cases: dict
    """
    corpus = []

    for key, case in cases.items():
        # get the file name and type or the defendant and complaintant
        c_file = case["complaintant"]["file"]
        c_type = case["complaintant"]["fileType"]
        d_file = case["defendant"]["file"]
        d_type = case["defendant"]["fileType"]

        # get the complaintant as a list of intervals
        complaintant = parse(DATA_DIR + "/" + c_file)
        # get the defendant as a list of intervals
        defendant = parse(DATA_DIR + "/" + d_file)

        if not vertical:
            # get the melodies
            c_melody = streamToIntervals(complaintant)
            d_melody = streamToIntervals(defendant)

            # add both works to the corpus
            corpus.append(c_melody)
            corpus.append(d_melody)
        else:
            # get the 'words' from the works
            c_words = parseMeasures(complaintant)
            d_words = parse(defendant)

            # add both works to the corpus
            corpus.append(c_words)
            corpus.append(d_words)

    return corpus

def parseMeasures(stream):
    """Takes a music21 stream and builds 'words' by grouping notes
    together that occur in the same measure. These 'words' are then
    tokenized to comprise a document

    :param stream: music21 stream
    :type stream: music21.Stream
    """
    max_time = stream.highestTime
    measure_time = 0
    measure_number = 0
    words = []
    while measure_time <= max_time:
        # isolate the next measure
        measure = stream.measures(measure_number, measure_number+1)
        if measure.highestTime == 0:
            # double safety catch. invalid measures can still be selected, but will have max time of zero
            break
        # get the pitches in the measure
        pitches = measure.flat.pitches
        # cast the pitches to ints and disregard octave
        pitches = sorted(set([pitch.diatonicNoteNum % 12 for pitch in pitches]))
        # want a string but need to differentiate 1,2 from 12
        words.append(".".join([str(p) for p in pitches]))
        # increment the measure number and take the highest time in the 
        # measure as the new measuretime
        measure_time = measure.highestTime
        measure_number += 1
    return words

helper = Music21Helper()

# build the dict of case pairings
cases = parseData(CASES_XML)

# optimize the size of the vectors
# vector_min, vector_max = getMaxIntervals(cases)
# returns -18,14
# will use -20,20 for now, static to save time
vector_min = -20
vector_max = 20

scores = []
# driver code for "horizontal" analysis
# convert music into vectors, pretty straight forward setup
'''
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

    # compute string matching similarities
    lcs_score = helper.lcsDP(c_melody, d_melody)
    lev_score = helper.levenshteinDistanceDP(c_melody, d_melody)

    # convert the interval list to a vector
    c_vector = intervalToVector(c_melody, vector_min, vector_max)
    d_vector = intervalToVector(d_melody, vector_min, vector_max)

    scores.append((lcs_score, lev_score))

    # instantiate a 'document ranker'
    ranker = Ranker(buildCorpus(cases), alpha=0.25, b=0.75, k=1.2, mu=0.75)
    # TODO - do some vector-based analysis
'''

# driver code for "vertical" analysis
# analyze groups of notes together. we will consider
# the group of notes that occur in a measure to be a "word."
# best approach is probably to get the notes, sort them, and
# represent as intervals. not sure how to standardize.

# build the 'vertical' corpus
# corpus = buildCorpus(cases, vertical=True)

scores = []

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

    # score by string matching techniques
    lcs_score = helper.lcsDP(c_words, d_words)
    lev_score = helper.levenshteinDistanceDP(c_words, d_words)

    scores.append((c_words, d_words))

    # instantiate a 'document ranker'
    ranker = Ranker(buildCorpus(cases), alpha=0.25, b=0.75, k=1.2, mu=0.75)
    # TODO - do some vector-based analysis
