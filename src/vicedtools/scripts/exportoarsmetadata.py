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
"""Executable script for exporting PAT test metadata from OARS."""

import json
import os

from vicedtools.acer import OARSSession
from vicedtools.scripts._config import (oars_tests_json, scale_constructs_json,
                                        oars_authenticator, oars_school_code)


def main():
    folder = os.path.dirname(oars_tests_json)
    if not os.path.exists(folder):
        os.makedirs(folder)
    folder = os.path.dirname(scale_constructs_json)
    if not os.path.exists(folder):
        os.makedirs(folder)

    s = OARSSession(oars_school_code, oars_authenticator)
    with open(oars_tests_json, 'w') as f:
        json.dump(s.tests, f)

    s = OARSSession(oars_school_code, oars_authenticator)
    with open(scale_constructs_json, 'w') as f:
        json.dump(s.scale_constructs, f)


if __name__ == "__main__":
    main()
