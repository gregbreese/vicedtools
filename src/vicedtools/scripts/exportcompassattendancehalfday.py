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
"""Executable script for exporting student attendance from Compass."""

import argparse
import datetime
import os

from vicedtools.compass import CompassSession
from vicedtools.scripts._config import (attendance_halfday_dir,
                                        compass_authenticator,
                                        compass_school_code)


def main():
    parser = argparse.ArgumentParser(
        description='Export student halfday attendance from Compass.')
    parser.add_argument(
        'start_date',
        help='the start date for the export, in yyyy-mm-dd format',
        type=datetime.date.fromisoformat)
    parser.add_argument(
        'finish_date',
        help='the finish date for the export, in yyyy-mm-dd format',
        type=datetime.date.fromisoformat)
    args = parser.parse_args()

    if not os.path.exists(attendance_halfday_dir):
        os.makedirs(attendance_halfday_dir)

    s = CompassSession(compass_school_code, compass_authenticator)
    s.export_attendance_cases_halfday(args.start_date, args.finish_date,
                                      attendance_halfday_dir)


if __name__ == "__main__":
    main()
