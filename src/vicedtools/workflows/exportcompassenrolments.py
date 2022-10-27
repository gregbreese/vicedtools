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
"""Executable script for exporting Compass enrolment metadata."""

import argparse
import json
import sys
import os

import pandas as pd

from vicedtools.compass.compasssession import CompassSession, CompassAuthenticator

if __name__ == "__main__":
    from config import (academic_groups_json, compass_authenticator,
                        compass_school_code, class_details_dir, 
                        enrolment_details_dir)
    if not os.path.exists(enrolment_details_dir):
        os.makedirs(enrolment_details_dir)

    parser = argparse.ArgumentParser(
        description='Export Compass class metadata.')
    parser.add_argument('academic_group',
                        type=int,
                        default=-1,
                        nargs='?',
                        help='the academic group to export')
    args = parser.parse_args()

    with open(academic_groups_json, 'r', encoding='utf-8') as f:
        cycles = json.load(f)
    if args.academic_group != -1:

        cycle_found = False
        for cycle in cycles:
            if cycle['id'] == args.academic_group:
                cycle_found = True
                cycle_name = cycle['name']
                break
        if not cycle_found:
            print("Academic group not found.")
            sys.exit(-2)
    else:
        for cycle in cycles:
            if cycle['isRelevant']:
                cycle_name = cycle['name']
                break

    filename = os.path.join(class_details_dir, f"{cycle_name} classes.json")
    with open(filename, "r", encoding='utf-8') as f:
        classes = json.load(f)
        
    s = CompassSession(compass_school_code, compass_authenticator)

    enrolments = []

    for c in classes[:20]:
        class_metadata = {"id":c["id"], "name":c["name"], "academic group":cycle_name}
        new_enrolments = s.get_class_enrolments(c["id"])
        for enrolment in new_enrolments:
            enrolment.update(class_metadata)
        enrolments += new_enrolments

    df = pd.DataFrame.from_records(enrolments)
    filename = os.path.join(enrolment_details_dir, f"{cycle_name} enrolments.csv")
    with open(filename, "w", encoding='utf-8') as f:
        df.to_csv(filename, index=False) 

    sys.exit(0)
