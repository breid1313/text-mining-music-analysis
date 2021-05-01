#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from pathlib import Path

DATA_DIR = os.path.abspath("./data_clean")
CASES_XML = Path(__file__).parent.parent / "data/dataset.xml"