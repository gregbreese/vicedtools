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
"""Executable script for exporting PAT sitting data from OARS."""

from datetime import date
import json
import os
import sys

from vicedtools.acer.oars import OARSAuthenticator, OARSSession

def export_oars_sittings(from_date: str, to_date: str, school_code: str, authenticator: OARSAuthenticator, export_dir: str = "."):
    """Exports completed PAT Sittings and saves them in sittings.json.

    Args:
        from_date: The start date to download results for in 
            dd-mm-yyyy format.
        to_date: The end date to download results for in dd-mm-yyyy format.
        school_code: An OARS school string. E.g. https://oars.acer.edu.au/{your school string}/...
        authenticator: An instance of OARSAuthenticator.
        export_dir: The directory to save the sittings data in.
    """
    export_file = os.path.join(export_dir, f"sittings {from_date} {to_date}.json")

    s = OARSSession(school_code, authenticator)
    sittings = s.get_all_pat_sittings(from_date, to_date)
    with open(export_file, 'w') as f:
        json.dump(sittings, f)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Received arguments were: ", sys.argv[1:])
        print("Required arguments are: from_date to_date")
        print("Dates to be given as dd-mm-yyyy")
        sys.exit(2)
    from_date = sys.argv[1]
    to_date = sys.argv[2]
    if to_date[2] != "-" or to_date[5] != "-" or from_date[2] != "-" or from_date[5] != "-":
        print("Dates must be formatted as dd-mm-yyyy")
        sys.exit(2)
    try:
        date(int(from_date[6:10]), int(from_date[3:5]), int(from_date[:2]))
        date(int(to_date[6:10]), int(to_date[3:5]), int(to_date[:2]))
    except ValueError:
        print("Dates must be formatted as dd-mm-yyyy")
        sys.exit(2)

    from config import (root_dir,
                        oars_folder,
                        sittings_folder,
                        oars_authenticator,
                        oars_school_code)

    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"{root_dir} does not exist as root directory.")
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"{root_dir} is not a directory.")
    oars_dir = os.path.join(root_dir, oars_folder)
    if not os.path.exists(oars_dir):
        os.mkdir(oars_dir)
    sittings_dir = os.path.join(oars_dir, sittings_folder)
    if not os.path.exists(sittings_dir):
        os.mkdir(sittings_dir)

    export_oars_sittings(from_date, to_date, oars_school_code, oars_authenticator, sittings_dir)