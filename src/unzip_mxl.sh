#! /bin/bash

cd "/Users/brianreid/grad school/research/music-plagiarism/data/dataset/cases"
for file in *.mxl; do
    unzip "${file}" -d "/Users/brianreid/xml-only"
done
