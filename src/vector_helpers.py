#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from collections import Counter
from math import inf

from music21.converter import Converter, parse

from constants import DATA_DIR, CASES_XML


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

    Returns a vector that represents how many times each interval
    occurs from the start param to the end param, for example:

    [0,0,0,0,0,0,0,2,5,3,10,12,7,8,3,1,0,0,1,0,0,0,0,0,0]

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

def buildCorpus(cases, vertical=False, vectors=False, vector_min=-30, vector_max=30):
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
            c = streamToIntervals(complaintant)
            d = streamToIntervals(defendant)

            if vectors:
                c = intervalToVector(c, vector_min, vector_max)
                d = intervalToVector(d, vector_min, vector_max)

        else:
            # get the 'words' from the works
            c = parseMeasures(complaintant)
            d = parseMeasures(defendant)

        # add both works to the corpus
        corpus.append(c)
        corpus.append(d)

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

def docToVector(doc, vocab):
    """converts a doc as a list of words to a vector where each item in the vector
    is the count of each word within the given document.

    :param doc: doc as a tokenized list of words
    :type doc: list
    :param vocab: dictionary-like object where the keys are all words in the vocab and the value is the count of appearances in the doc
    :type vocab: Counter or dict
    """
    vector = []
    doc = Counter(doc)
    for word in vocab:
        vector.append(doc[word])
    return vector
