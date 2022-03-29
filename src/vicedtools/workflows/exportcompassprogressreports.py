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

import sys
import os

from vicedtools.compass import CompassWebDriver, CompassAuthenticator


def export_compass_progress_reports(gecko_path: str, school_code: str,
                                    authenticator: CompassAuthenticator,
                                    progress_reports_dir: str, cycle: str):
    """Exports a single Compass reports cycle.

    Args:
        gecko_path: The path to geckodiver.exe
        school_code: The compass school string. E.g. https://{school_code}.compass.education
        authenticator: An instance of CompassAuthenticator.
        progress_reports_dir: The directory to save progress reports data to.
        cycle: The name of the progress report cycle to export.
    """
    driver = CompassWebDriver(school_code, gecko_path, authenticator)
    driver.export_progress_report(cycle, download_path=progress_reports_dir)
    driver.quit()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Received arguments were: ", sys.argv[1:])
        print('Requires one argument: cycle')
        sys.exit(2)
    cycle = sys.argv[1]

    from config import (root_dir, compass_folder, progress_reports_folder,
                        gecko_path, compass_authenticator, compass_school_code)

    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"{root_dir} does not exist as root directory.")
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"{root_dir} is not a directory.")
    compass_dir = os.path.join(root_dir, compass_folder)
    if not os.path.exists(compass_dir):
        os.mkdir(compass_dir)
    progress_reports_dir = os.path.join(compass_dir, progress_reports_folder)
    if not os.path.exists(progress_reports_dir):
        os.mkdir(progress_reports_dir)

    export_compass_progress_reports(gecko_path, compass_school_code,
                                    compass_authenticator, progress_reports_dir,
                                    cycle)
