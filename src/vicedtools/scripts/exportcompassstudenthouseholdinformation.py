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
"""Executable script for exporting student household data from Compass."""

import os

from vicedtools.compass import CompassSession
from vicedtools.scripts._config import (student_household_information_csv,
                                        compass_authenticator,
                                        compass_school_code)


def main():
    folder = os.path.dirname(student_household_information_csv)
    if not os.path.exists(folder):
        os.makedirs(folder)

    s = CompassSession(compass_school_code, compass_authenticator)
    s.export_student_household_information(
        file_name=student_household_information_csv)


if __name__ == "__main__":
    main()
