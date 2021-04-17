#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

# CASE_FILE = Path(__file__).parent.parent / "./data/dataset.xml"

"""
This file contains the logic to read the dataset xml file into Python dictionaries.
Each key in the dictionary is the year of a music plagiarism lawsuit and the artists names
involved. Under each key is the information necessary to pass to music21 in order to parse
the music file into a Score or Stream (file name and file type) as well as the song title
and the artist name.


results will look like the following
{
    "1933/artist1/artist2": {
        "compaintant": {
            "song": foo,
            "artist": artist1,
            "file": bar,
            "fileType": mxl
        },
        "defendant": {
            "song": foo2,
            "artist": artist2,
            "file": bar2,
            "fileType": mxl
        }
    },
    .
    .
    .
}
"""

def parseCase(node):
    """Takes a dwork or cwork node and parses out the
    artist name, song title, file type and file name.
    Returns those values as a dictionary.

    :param node: xml tree case node
    :type node: xml.Element
    :return: cwork or dwork data
    :rtype: dict
    """

    artist = node.find("./artist")
    title = node.find("./songtitle")
    fileType = node.find("./datatype")
    fileName = node.find("./filename")

    extension = None
    if fileType.text.lower() == "mxl":
        extension = "xml"
    elif fileType.text.lower() == "midi":
        extension = "mid"
    else:
        # don't know how to handle this
        extension = fileType.text.lower()

    return {
            "song": title.text,
            "artist": artist.text,
            "file": fileName.text + "." + extension,
            "fileType": fileType.text
    }

def parseData(filePath):
    """Takes a file path to an xml file and parses out the dwork
    and cwork data. Dependends on a pre-defined xml tree structure of
    <cases>
        <case>
                <year>1933</year>
                <cwork>
                <artist>Ira Arnstein</artist>
                <songtitle>Light My Life With Love</songtitle>
                <datatype>MXL</datatype>
                <filename>light_myLife</filename>
                </cwork>

                <dwork>
                <artist>Nathaniel Shilkret</artist>
                <songtitle>Lady Divine</songtitle>
                <datatype>MXL</datatype>
                <filename>lady_divine_pt1</filename>
                </dwork>               
        </case>
        ...
        <case></case>
    </cases>
    :param filePath: file path to the target xml file
    :type filePath: str
    :return: dictionary of case data
    :rtype: defaultdict
    """
    result = defaultdict(defaultdict)

    tree = ET.parse(filePath)
    root = tree.getroot()

    cases = root.findall("./case")
    for case in cases:
        year = case.find("./year")
        complaintant = case.find("./cwork")
        defendant = case.find("./dwork")

        complaintant_dict = parseCase(complaintant)
        defendant_dict = parseCase(defendant)

        key = "{0}/{1}/{2}".format(year.text, complaintant_dict["artist"], defendant_dict["artist"])

        result[key]["complaintant"] = complaintant_dict
        result[key]["defendant"] = defendant_dict

    return result

def buildFileList(filePath):
    """build a list of all song files that are available to us from the dataset.
    This is useful when we don't necessarily want to just look at songs that are
    involved in litigation together. If time complexity were important, we could
    interpolate this from parseData(), but for simplicity's sake this is ok.

    :param filePath: path to the case data
    :type filePath: str
    """

    result = defaultdict(defaultdict)

    tree = ET.parse(filePath)
    root = tree.getroot()

    cases = root.findall("./case")
    for case in cases:
        complaintant = case.find("./cwork")
        defendant = case.find("./dwork")

        # gather the data for each work
        complaintant_dict = parseCase(complaintant)
        defendant_dict = parseCase(defendant)

        # store each work with its title as the key
        result[complaintant_dict["song"]] = complaintant_dict
        result[defendant_dict["song"]] = defendant_dict

        # add the case pairing in case we want to access it later
        # space complexity is not a concern, so we can be liberal with the data structure
        # store under the "litigation" key
        result[complaintant_dict["song"]]["litigation"] = defendant_dict
        result[defendant_dict["song"]]["litigation"] = complaintant_dict

    return result
