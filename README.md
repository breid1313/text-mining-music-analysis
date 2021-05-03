# Analysis of Music Plagiarism Through Text Mining Techniques

## Sub Modules
This repository depends on two sub-modules. To execute the Python files in this repository, you will need to checkout both submodules into the proper directory
using the following two commands:

`git submodule add git@github.com:breid1313/document-ranker.git  src/lib/document_ranker`

`git submodule add git@github.com:breid1313/midi-levenshtein-lcs.git  src/lib/midi_levenshtein_lcs`

## Data

### data/
Compressed .mxl format.

### data-clean/
Expanded .xml or .mid format.


## Results

### Horizontal
horizontal final results:
LCS max: 0.7021276595744681
LCS min: 0.5531914893617021
LCS avg: 0.623404255319149


Lev max: 0.3191489361702128
Lev min: 0.1702127659574468
Lev avg: 0.24255319148936172


BM25 max: 0.6170212765957447
BM25 min: 0.44680851063829785
BM25 avg: 0.5


PLN max: 0.6170212765957447
PLN min: 0.44680851063829785
PLN avg: 0.5085106382978724


### Vertical 
vertical final results:
LCS max: 0.5319148936170213
LCS min: 0.3829787234042553
LCS avg: 0.4659574468085107


Lev max: 0.3191489361702128
Lev min: 0.19148936170212766
Lev avg: 0.23404255319148937


BM25 max: 0.5319148936170213
BM25 min: 0.44680851063829785
BM25 avg: 0.48936170212765956


PLN max: 0.5531914893617021
PLN min: 0.46808510638297873
PLN avg: 0.5021276595744681