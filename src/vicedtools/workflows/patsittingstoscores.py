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


def pat_sittings_to_scores(oars_dir: str, sittings_folder: str = "sittings"):

    sittings_dir = os.path.join(oars_dir, sittings_folder)
    if not os.path.exists(sittings_dir):
        FileNotFoundError(f"{sittings_dir} does not exist as directory.")
    # import test metadata
    tests_file = os.path.join(oars_dir, "tests.json")
    with open(tests_file, 'r', encoding='utf-8') as fp:
        tests = json.load(fp)
    tests = PATTests(tests)
    # import all settings exports and combine
    filenames = glob.glob(os.path.join(sittings_dir, "sittings*.json"))
    sittings = PATSittings([])
    for filename in filenames:
        print(filename)
        with open(filename, 'r', encoding='utf-8') as fp:
            temp = json.load(fp)
        sittings.extend(PATSittings(temp))
    # export summary
    df = sittings.summary(tests)
    export_file = os.path.join(oars_dir, "pat scores.csv")
    df.to_csv(export_file, index=False)


if __name__ == "__main__":
    from config import (root_dir,
                        oars_folder,
                        sittings_folder)

    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"{root_dir} does not exist as root directory.")
    oars_dir = os.path.join(root_dir, oars_folder)
    if not os.path.exists(oars_dir):
        raise FileNotFoundError(f"{oars_dir} does not exist as a directory.")
    pat_sittings_to_scores(oars_dir, sittings_folder)

