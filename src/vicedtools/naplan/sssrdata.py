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
"""A class for extracting data from the NAPLAN SSSR data.js file."""

import requests
import time
import urllib3
import os.path

import demjson
import numpy as np
import pandas as pd


class SSSRdata:
    """A class for extracting data from the NAPLAN SSSR data.js file.
    
    Attributes:
        data: A dictionary containing the raw data from the data.js file.
        domains: A DataFrame containing metadata about NAPLAN test domains.
        subdomains: A DataFrame containing metadata about NAPLAN test subdomains.
        questions: A DataFrame containing metadata about NAPLAN test questions.
        responses: A DataFrame containing the individual item responses for
            all students.
        bands: A DataFrame containing band cutoff metadata for each test.
    """

    def __init__(self, js_file: str):
        """Parses the data contained in the data.js file.
        
        Args:
            js_file: The path to the SSSR data.js file.
        """
        with open(js_file, 'r', encoding='utf8') as f:
            js_data = f.readline()
        self.data = demjson.decode(js_data[11:])

        self.domains = pd.DataFrame(self.data['domains'])
        self.domains.set_index("domainId", inplace=True)
        self.subdomains = pd.DataFrame(self.data['subdomains'])
        self.subdomains.set_index("domainId", inplace=True)
        self.questions = pd.DataFrame(self.data['questions'])

        # corrects an error in the data file
        try:
            self.questions.loc[
                "d797f974-0ff3-e811-80c0-0003ff85e991",
                "exemplarItem"] = self.questions.iloc[1476]["exemplarItem"]
        except KeyError:
            pass

        self.questions[
            "exemplarItemImageURL"] = "https://assessform.edu.au/Resources/Public/Ex/" + self.questions[
                "exemplarItem"].str[-9:] + ".png"
        self.questions["exemplarItemImageFile"] = self.questions[
            "exemplarItem"].str[-9:] + ".png"

        self.bands = extract_bands_info(self.data['testLevelBandsInfo'])

        extracted_attempts = np.concatenate([
            extract_attempt_details(attempt)
            for attempt in self.data['attempts']
        ])
        self.responses = pd.DataFrame.from_records(extracted_attempts)
        self.responses = pd.merge(
            self.responses,
            self.questions[["eventIdentifier", "difficulty"]],
            on=["questionId", "eventIdentifier"])
        self.responses["scaledScore"] = self.responses["scaledScore"].astype(
            float)
        self.responses['scaleDelta'] = self.responses[
            'scaledScore'] - self.responses["difficulty"]
        self.responses['correctScore'] = self.responses['correct'].apply(
            lambda a: 1 if a else 0)

    def download_exemplar_images(self, path: str):
        """Downloads the images for exemplar test items to the given path.
        
        Attempts to download all test items. Skips items that have already been
        downloaded. Images are named with the corresponding question 
        identifier.

        Args:
            path: The folder to save the images in.
        """
        urllib3.disable_warnings()

        if path[-1] not in {'/', '\\'}:
            path += '/'
        for index, row in self.questions.iterrows():
            if type(row["exemplarItemImageFile"]) is str:
                filename = path + row["exemplarItemImageFile"]
                if not os.path.isfile(filename):
                    img_data = requests.get(row["exemplarItemImageURL"],
                                            verify=False).content
                    with open(filename, 'wb') as handler:
                        handler.write(img_data)
                    time.sleep(0.1)


def extract_bands_info(bands_info):
    bands = []
    for test_level in bands_info:
        for discipline in bands_info[test_level]:
            for band in bands_info[test_level][discipline]:
                extract = dict()
                for key in [
                        'band', 'bandStartPoint', 'scoreCutPoint',
                        'disciplineId'
                ]:
                    extract[key] = band[key]
                bands.append(extract)
    df = pd.DataFrame.from_records(bands)
    return df.drop_duplicates()


def extract_attempt_details(attempt):
    eventIdentifier = attempt['eventIdentifier']
    studentId = attempt['student']['studentId']
    try:
        schoolStudentId = attempt['student']['metadata']['schoolStudentId']
    except KeyError:
        schoolStudentId = ""
    testLevel = attempt['student']['testLevel']
    domainName = attempt['domain']['domainName']
    scaledScore = attempt['scaledScore']
    disciplineId = attempt['disciplineId']
    extracted_answers = []
    for answer in attempt['answers']:
        extracted_answer = {
            'eventIdentifier': eventIdentifier,
            'studentId': studentId,
            'schoolStudentId': schoolStudentId,
            'testLevel': testLevel,
            'domainName': domainName,
            'scaledScore': scaledScore,
            'disciplineId': disciplineId
        }
        for key in [
                'correct', 'questionNo', 'questionId', 'questionIdentifier',
                'performance', 'writingResponse', 'markingSchemeComponents'
        ]:
            extracted_answer[key] = answer[key]
        extracted_answers.append(extracted_answer)
    return extracted_answers
