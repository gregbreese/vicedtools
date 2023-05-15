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
"""Executable script for exporting staff details from OARS."""

import json
import os

from vicedtools.acer import OARSSession
from vicedtools.scripts._config import (oars_staff_xlsx, oars_authenticator,
                                        oars_school_code)


def main():
    parent_dir = os.path.dirname(oars_staff_xlsx)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    s = OARSSession(oars_school_code, oars_authenticator)
    s.get_staff_xlsx(oars_staff_xlsx)


if __name__ == "__main__":
    main()
