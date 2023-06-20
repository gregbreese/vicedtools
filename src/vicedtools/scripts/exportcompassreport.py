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
"""Executable script for exporting Compass reports data."""

from __future__ import annotations

import argparse
import json
import os

from vicedtools.compass import CompassSession, get_report_cycle_id
from vicedtools.scripts.config import (reports_dir, compass_authenticator,
                                        compass_school_code, report_cycles_json)


def main():
    parser = argparse.ArgumentParser(
        description='Export all Compass progress reports.')
    parser.add_argument('year', type=int, help='the report year')
    parser.add_argument('title', help='the report title')
    args = parser.parse_args()

    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    with open(report_cycles_json, 'r', encoding='utf-8') as f:
        cycles = json.load(f)

    cycle_id = get_report_cycle_id(cycles, args.year, args.title)
    s = CompassSession(compass_school_code, compass_authenticator)
    s.export_reports(cycle_id, args.year, args.title, save_dir=reports_dir)


if __name__ == "__main__":
    main()
