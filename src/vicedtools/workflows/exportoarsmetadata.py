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
"""Executable script for exporting PAT test metadata from OARS."""

import json
import os

from vicedtools.acer.oars import OARSSession


def export_oars_metadata(school_code, authenticator, oars_tests_json,
                         scale_constructs_json):
    """Exports PAT test metadata.
    
    Saves test metadata in tests.json.
    Saves scale construct metadata in scaleconstructs.json

    Args:
        school_code: An OARS school string. E.g. https://oars.acer.edu.au/{your school string}/...
        authenticator: An instance of OARSAuthenticator.
        oars_tests_json: The filename to save the test metadata.
        scale_constructs_json: The filename to save the scale construct metadata
    """
    s = OARSSession(oars_school_code, oars_authenticator)
    with open(oars_tests_json, 'w') as f:
        json.dump(s.tests, f)

    s = OARSSession(oars_school_code, oars_authenticator)
    with open(scale_constructs_json, 'w') as f:
        json.dump(s.scale_constructs, f)


if __name__ == "__main__":
    from config import (oars_tests_json, scale_constructs_json,
                        oars_authenticator, oars_school_code)

    folder = os.path.dirname(oars_tests_json)
    if not os.path.exists(folder):
        os.makedirs(folder)
        folder = os.path.dirname(scale_constructs_json)
    if not os.path.exists(folder):
        os.makedirs(folder)

    export_oars_metadata(oars_school_code, oars_authenticator, oars_tests_json,
                         scale_constructs_json)
