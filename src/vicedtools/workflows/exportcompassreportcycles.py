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
"""Executable script for exporting Compass report cycles."""

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

    :meta private:
    """
    s = CompassSession(school_code, authenticator)
    cycles = s.get_report_cycles()
    with open(file_name, "w", encoding='utf-8') as f:
        json.dump(cycles, f)


if __name__ == "__main__":
    from config import (report_cycles_json, compass_authenticator,
                        compass_school_code)
    parent_dir = os.path.dirname(report_cycles_json)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    export_compass_report_cycles(compass_school_code, compass_authenticator,
                                 report_cycles_json)
    sys.exit(0)
