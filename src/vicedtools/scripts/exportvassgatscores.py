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
"""Executable script for exporting gat score data from VASS."""

import argparse
import os

from vicedtools.vce import VASSSession
from vicedtools.scripts.config import (vass_authenticator, vass_gat_scores_dir)


def main():
    parser = argparse.ArgumentParser(description='Export VASS gat scores.')
    parser.add_argument('years',
                        nargs='+',
                        help='the year to download the scores for.')
    args = parser.parse_args()

    if not os.path.exists(vass_gat_scores_dir):
        os.makedirs(vass_gat_scores_dir)

    driver = VASSSession(vass_authenticator)

    for year in args.years:
        driver.change_year(year)
        file_name = os.path.join(vass_gat_scores_dir, f"gat scores {year}.csv")
        driver.gat_summary(file_name)


if __name__ == "__main__":
    main()