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
"""Executable script for exporting NAPLAN outcomes from VCAA data service."""

from __future__ import annotations

import argparse
import os

from vicedtools.naplan import DataserviceSession
from vicedtools.scripts._config import (naplan_sssr_dir,
                                        dataservice_authenticator)


def main():
    parser = argparse.ArgumentParser(
        description='Export NAPLAN outcomes from VCAA data service')
    parser.add_argument('years',
                        nargs='+',
                        type=int,
                        help='the years to export')
    args = parser.parse_args()

    if not os.path.exists(naplan_sssr_dir):
        os.makedirs(naplan_sssr_dir)

    s = DataserviceSession(dataservice_authenticator)

    for year in args.years:
        s.export_sssr(year, naplan_sssr_dir)


if __name__ == "__main__":
    main()
