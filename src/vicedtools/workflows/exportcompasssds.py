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

import os

import pandas as pd

from vicedtools.compass import CompassWebDriver, CompassAuthenticator


def export_compass_sds(gecko_path: str, school_code: str,
                       authenticator: CompassAuthenticator, export_dir: str):
    """Exports student details from Compass.

    Args:
        gecko_path: The path to geckodiver.exe
        school_code: The compass school string. E.g. https://{school_code}.compass.education
        authenticator: An instance of CompassAuthenticator.
        export_dir: The folder to save the SDS export data to.
    """
    driver = CompassWebDriver(school_code, gecko_path, authenticator)
    driver.export_sds(export_dir)
    driver.quit()


if __name__ == "__main__":
    from config import (root_dir, compass_folder, sds_folder, gecko_path,
                        compass_authenticator, compass_school_code)

    if not os.path.exists(root_dir):
        raise FileNotFoundError(f"{root_dir} does not exist as root directory.")
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"{root_dir} is not a directory.")
    compass_dir = os.path.join(root_dir, compass_folder)
    if not os.path.exists(compass_dir):
        os.mkdir(compass_dir)
    sds_dir = os.path.join(compass_dir, sds_folder)
    if not os.path.exists(sds_dir):
        os.mkdir(sds_dir)

    export_compass_sds(gecko_path, compass_school_code, compass_authenticator,
                       sds_dir)
