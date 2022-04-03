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
"""Executable script for exporting Compass progress report data."""

import json
import sys
import os

from vicedtools.compass.compasssession import CompassSession, CompassAuthenticator


def export_compass_report_cycles(school_code: str,
                                 authenticator: CompassAuthenticator,
                                 file_name: str):
    """Exports metadata for Compass report cycles to a json file.

    Args:
        school_code: The compass school string. E.g. https://{school_code}.compass.education
        authenticator: An instance of CompassAuthenticator.
        file_name: The file name to save the json data to
    """
    s = CompassSession(school_code, authenticator)
    cycles = s.get_report_cycles()
    with open(file_name, "w", encoding='utf-8') as f:
        json.dump(cycles, f)


if __name__ == "__main__":
    from config import (root_dir, compass_folder, report_cycles_json,
                        compass_authenticator, compass_school_code)
    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"{root_dir} does not exist as root directory.")
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"{root_dir} is not a directory.")
    compass_dir = os.path.join(root_dir, compass_folder)
    if not os.path.exists(compass_dir):
        os.mkdir(compass_dir)
    file_name = os.path.join(root_dir, compass_folder, report_cycles_json)

    export_compass_report_cycles(compass_school_code, compass_authenticator,
                                 file_name)
    sys.exit(0)
