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
"""Utility functions for working with eWrite results exports."""

COLUMNS = [
    'Family name', 'Given name', 'Middle name', 'Username', 'Gender',
    'Year level (at time of test)', 'Tags (at time of test)', 'Date', 'Score',
    'Scale', 'Band', 'OE', 'TS', 'ID', 'VOC', 'PARA', 'SENT', 'SPUNC', 'PINS',
    'SP', 'Response'
]

SCORE_TO_SCALE = {
    'ID': {
        1: 285.0,
        2: 445.0,
        3: 580.0
    },
    'OE': {
        1: 265.0,
        2: 390.0,
        3: 480.0,
        4: 590.0
    },
    'PARA': {
        1: 360.0,
        2: 475.0,
        3: 615.0
    },
    'PINS': {
        1: 420.0,
        2: 545.0
    },
    'SENT': {
        1: 280.0,
        2: 400.0,
        3: 500.0,
        4: 620.0
    },
    'SP': {
        1: 230.0,
        2: 345.0,
        3: 465.0,
        4: 565.0
    },
    'SPUNC': {
        1: 340.0,
        2: 455.0
    },
    'TS': {
        1: 310.0,
        2: 440.0,
        3: 570.0
    },
    'VOC': {
        1: 305.0,
        2: 450.0,
        3: 575.0
    },
}
