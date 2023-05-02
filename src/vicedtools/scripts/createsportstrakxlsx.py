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
"""Executable script for uploading compass reports to BigQuery."""

from datetime import datetime
import os

from vicedtools.sportstrak import create_sportstrak_student_import
from vicedtools.scripts._config import (config, sportstrak_dir, student_details_csv)


def main():
    if not os.path.exists(sportstrak_dir):
        os.makedirs(sportstrak_dir)

    date_today = datetime.today().strftime('%Y-%m-%d')
    destination_xlsx = os.path.join(sportstrak_dir, f"{date_today} sportstrak export.xlsx")
    create_sportstrak_student_import(student_details_csv,
                                     destination_xlsx,
                                     config["sportstrak"]["house_map"])



if __name__ == "__main__":
    main()
