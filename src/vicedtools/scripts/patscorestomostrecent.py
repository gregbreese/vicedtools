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
"""Executable script for creating a summary of student's most recent PAT scores."""

import os

import pandas as pd

from vicedtools.scripts._config import (pat_scores_csv, pat_most_recent_csv)


def main():
    summary_df = pd.read_csv(pat_scores_csv)
    # get only most recent result for each test
    summary_df.sort_values("Completed", ascending=False, inplace=True)
    summary_df.drop_duplicates(subset=["Username", "Test"], inplace=True)

    recent_wide = summary_df.pivot(index="Username", columns="Test")
    recent_wide.columns = [f"{b} {a}" for (a, b) in recent_wide.columns]
    recent_wide.reset_index(inplace=True)

    recent_wide.to_csv(pat_most_recent_csv, index=False)


if __name__ == "__main__":
    main()
