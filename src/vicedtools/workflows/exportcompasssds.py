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
"""Executable script for exporting the SDS export from Compass."""

import argparse
import json
import os
import sys

from vicedtools.compass import CompassSession

if __name__ == "__main__":
    from config import (sds_dir, compass_authenticator, compass_school_code,
                        academic_groups_json)

    parser = argparse.ArgumentParser(
        description='Export the SDS export from Compass')
    parser.add_argument(
        '-academicgroup',
        help='the name of the academic group, for example "2022 Academic"')
    args = parser.parse_args()

    if args.academicgroup:
        with open(academic_groups_json, 'r', encoding='utf-8') as f:
            academic_groups = json.load(f)
        for g in academic_groups:
            academic_group_id = None
            if g['name'] == args.academicgroup:
                academic_group_id = g['id']
                break
        if not academic_group_id:
            print("Academic group name not found.")
            sys.exit(3)
        save_dir = os.path.join(sds_dir, args.academicgroup)
        os.makedirs(save_dir)
        s = CompassSession(compass_school_code, compass_authenticator)
        s.export_sds(save_dir=save_dir, academic_group=academic_group_id)
    else:
        if not os.path.exists(sds_dir):
            os.makedirs(sds_dir)

        s = CompassSession(compass_school_code, compass_authenticator)
        s.export_sds(save_dir=sds_dir)
