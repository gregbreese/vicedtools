#!/usr/bin/env python

# Copyright 2023 VicEdTools authors

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Executable script for exporting Compass subject metadata."""

from __future__ import annotations

import argparse
import json
import os
import time

import pandas as pd

from vicedtools.compass import CompassSession, sanitise_filename
from vicedtools.scripts.config import (compass_authenticator,
                                        compass_school_code,
                                        academic_groups_json, subjects_dir)


def main():
    parser = argparse.ArgumentParser(
        description='Export all Compass subject metadata.')
    parser.add_argument(
        '--forceall',
        '-a',
        action="store_true",
        help='force re-download existing subject metadata exports')
    parser.add_argument('--forcecurrent',
                        '-c',
                        action="store_true",
                        help='force re-download current academic cycle')
    args = parser.parse_args()

    if not os.path.exists(subjects_dir):
        os.makedirs(subjects_dir)

    with open(academic_groups_json, 'r', encoding='utf-8') as f:
        cycles = json.load(f)

    s = CompassSession(compass_school_code, compass_authenticator)

    for cycle in cycles:
        sanitised_name = sanitise_filename(cycle['name'])
        file_name = os.path.join(subjects_dir, f"Subjects-{sanitised_name}.csv")
        if not os.path.exists(file_name) or args.forceall or (
                args.forcecurrent and cycle['isRelevant']):
            print(f"Exporting {cycle['name']}")
            subjects = s.get_subjects(cycle['id'])
            subjects_df = pd.DataFrame.from_records(subjects)
            subjects_df.to_csv(file_name)
            time.sleep(3)


if __name__ == "__main__":
    main()
