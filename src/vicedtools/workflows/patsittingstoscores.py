# Copyright 2021 VicEdTools authors

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Executable script for creating a table of student PAT scores."""

import glob
import json
import os

import pandas as pd

from vicedtools.acer import PATTests, PATSittings


def pat_sittings_to_scores(oars_tests_json: str, pat_sittings_dir: str,
                           pat_scores_csv: str):
    # import test metadata
    with open(oars_tests_json, 'r', encoding='utf-8') as fp:
        tests = json.load(fp)
    tests = PATTests(tests)
    # import all settings exports and combine
    filenames = glob.glob(os.path.join(pat_sittings_dir, "sittings*.json"))
    sittings = PATSittings([])
    for filename in filenames:
        print(filename)
        with open(filename, 'r', encoding='utf-8') as fp:
            temp = json.load(fp)
        sittings.extend(PATSittings(temp))
    # export summary
    df = sittings.summary(tests)

    folder = os.path.dirname(pat_scores_csv)
    if not os.path.exists(folder):
        os.makedirs(folder)
    df.to_csv(pat_scores_csv, index=False)


if __name__ == "__main__":
    from config import (oars_tests_json, pat_sittings_dir, pat_scores_csv)

    pat_sittings_to_scores(oars_tests_json, pat_sittings_dir, pat_scores_csv)
