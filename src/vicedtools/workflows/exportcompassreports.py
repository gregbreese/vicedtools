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
"""Executable script for exporting Compass reports data."""

import sys
import os

from vicedtools.compass import CompassWebDriver, CompassAuthenticator


def export_compass_reports(gecko_path: str, school_code: str,
                           authenticator: CompassAuthenticator,
                           reports_dir: str, year: str, title: str):
    """Exports a single Compass reports cycle.

    Args:
        gecko_path: The path to geckodiver.exe
        school_code: The compass school string. E.g. https://{school_code}.compass.education
        authenticator: An instance of CompassAuthenticator.
        reports_dir: The directory to save reports data to
        year: The year of the report cycle to export, as a string.
        title: The title of the report cycle to export.
    """
    driver = CompassWebDriver(school_code, gecko_path, authenticator)
    driver.export_report_cycle(year, title, download_path=reports_dir)
    driver.quit()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Received arguments were: ", sys.argv[1:])
        print('Requires two arguments: year title')
        sys.exit(2)
    year = sys.argv[1]
    title = sys.argv[2]

    from config import (root_dir, compass_folder, reports_folder, gecko_path,
                        compass_authenticator, compass_school_code)

    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"{root_dir} does not exist as root directory.")
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"{root_dir} is not a directory.")
    compass_dir = os.path.join(root_dir, compass_folder)
    if not os.path.exists(compass_dir):
        os.mkdir(compass_dir)
    reports_dir = os.path.join(compass_dir, reports_folder)
    if not os.path.exists(reports_dir):
        os.mkdir(reports_dir)

    export_compass_reports(gecko_path, compass_school_code,
                           compass_authenticator, reports_dir, year, title)
