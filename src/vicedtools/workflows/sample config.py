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
"""A sample configuration file."""

# gecko path
gecko_path = "geckodriver.exe"

root_dir = "."

# compass
from vicedtools.compass import CompassFirefoxCookieAuthenticator
compass_authenticator = CompassFirefoxCookieAuthenticator()
compass_school_code = "abcsc-vic"
compass_folder = "compass exports"
student_details_folder = "student details"
student_details_csv = "student details.csv"
sds_folder = "SDS export"

# oars
from vicedtools.acer import OARSFirefoxCookieAuthenaticator
oars_authenticator = OARSFirefoxCookieAuthenaticator()
oars_school_code = "abc-secondary-college"
oars_folder = "OARS exports"
sittings_folder = "sittings"

# gcp
student_details_table_id = "abc-school-data.student_details.student_details"
student_enrolments_table_id = "abc-school-data.student_details.student_enrolments"
pat_scores_table_id = "abc-school-data.student_results.pat_scores"
pat_most_recent_table_id = "abc-school-data.student_results.pat_most_recent"
bucket = "abc-bucket"

