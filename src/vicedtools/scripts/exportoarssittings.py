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
"""Executable script for exporting PAT sitting data from OARS."""

from datetime import date
import json
import os
import sys

from vicedtools.acer import OARSAuthenticator, OARSSession
from vicedtools.scripts.config import (pat_sittings_dir, ewrite_sittings_dir,
                                       oars_candidates_json, 
                                       oars_authenticator, oars_school_code)


def main():
    if len(sys.argv) != 3:
        print("Received arguments were: ", sys.argv[1:])
        print("Required arguments are: from_date to_date")
        print("Dates to be given as dd-mm-yyyy")
        sys.exit(2)
    #else: # grab results from most recent end date to yesterday

    from_date = sys.argv[1]
    to_date = sys.argv[2]
    if to_date[2] != "-" or to_date[5] != "-" or from_date[
            2] != "-" or from_date[5] != "-":
        print("Dates must be formatted as dd-mm-yyyy")
        sys.exit(2)
    try:
        date(int(from_date[6:10]), int(from_date[3:5]), int(from_date[:2]))
        date(int(to_date[6:10]), int(to_date[3:5]), int(to_date[:2]))
    except ValueError:
        print("Dates must be formatted as dd-mm-yyyy")
        sys.exit(2)

    s = OARSSession(oars_school_code, oars_authenticator)

    # Export the requested PAT sittings data
    if not os.path.exists(pat_sittings_dir):
        os.makedirs(pat_sittings_dir)
    export_file = os.path.join(pat_sittings_dir,
                               f"sittings {from_date} {to_date}.json")

    sittings = s.get_all_pat_sittings(from_date, to_date)
    with open(export_file, 'w') as f:
        json.dump(sittings, f)

    # Export the requested eWrite sittings data
    if not os.path.exists(ewrite_sittings_dir):
        os.makedirs(ewrite_sittings_dir)
    export_file = os.path.join(ewrite_sittings_dir,
                               f"sittings {from_date} {to_date}.json")

    with open(oars_candidates_json, 'r') as f:
        candidates = json.load(f)
    sittings = s.get_ewrite_sittings(candidates, from_date, to_date)
    with open(export_file, 'w') as f:
        json.dump(sittings, f)


if __name__ == "__main__":
    main()
