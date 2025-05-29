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

import json
import requests
import time
import urllib3
import os.path

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
    """

    def __init__(self, js_file: str):
        """Parses the data contained in the data.js file.
        
        Args:
            js_file: The path to the SSSR data.js file.
        """
        with open(js_file, 'r', encoding='utf8') as f:
            js_data = f.readline()
        self.data = json.loads(js_data[11:])

        self.domains = pd.DataFrame(self.data['domains'])
        self.domains.set_index("domainId", inplace=True)
        self.subdomains = pd.DataFrame(self.data['subdomains'])
        self.subdomains.set_index("domainId", inplace=True)
        self.questions = pd.DataFrame(self.data['questions'])

        self.questions[
            "exemplarItemImageURL"] = "https://assessform.edu.au/Resources/Public/Ex/" + self.questions[
                "exemplarItem"].str[-9:] + ".png"
        self.questions["exemplarItemImageFile"] = self.questions[
            "exemplarItem"].str[-9:] + ".png"

        extracted_attempts = np.concatenate([
            extract_attempt_details(attempt)
            for attempt in self.data['attempts']
        ])
        self.responses = pd.DataFrame.from_records(extracted_attempts)
        self.responses = pd.merge(
            self.responses,
            self.questions[["questionId", "eventIdentifier", "difficulty"]],
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
        for _index, row in self.questions.iterrows():
            if type(row["exemplarItemImageFile"]) is str:
                filename = path + row["exemplarItemImageFile"]
                if not os.path.isfile(filename):
                    img_data = requests.get(row["exemplarItemImageURL"],
                                            verify=False).content
                    with open(filename, 'wb') as handler:
                        handler.write(img_data)
                    time.sleep(0.1)


    def export_outcome_levels(self, csv_file):
        """Creates an Outcome Levels csv export.
        
        Exports each students overall results in all tests in a csv using the
        same format as the NAPLAN Outcome Levels export.

        Args:
            csv_file: The path to save the export to.
        """
        records = []
        for attempt in self.data['attempts']:
            record = {}
            record["First Name"] = attempt['student']['studentFirstName']
            record[" Surname"] = attempt['student']['studentLastName']
            record[" Reporting Test"] = "YR" + attempt['student']['testLevel'] + "O"
            try:
                record['Cases ID'] = attempt['student']['metadata']['schoolStudentId']
            except KeyError:
                record['Cases ID'] = ""
            record['domain'] = attempt['domain']['domainName']
            record['scaledScore'] = attempt['scaledScore']
            records.append(record)
        df = pd.DataFrame.from_records(records)

        df['domain'] = df['domain'].str.upper()
        df['domain'] = df['domain'].str.replace('AND', '&')
        output = df.pivot(index=["Cases ID", "First Name", " Surname", " Reporting Test"], columns="domain", values="scaledScore").reset_index()

        # make missing columns and save with columns in correct order
        fields = ['APS Year', ' Reporting Test', 'First Name', ' Second Name', ' Surname',
            'READING', 'WRITING', 'SPELLING', 'NUMERACY', 'GRAMMAR & PUNCTUATION',
            'Home Group', 'Date of birth', 'Gender', 'LBOTE', 'ATSI',
            'Home School Name', 'Reporting School Name', 'Cases ID']

        output['APS Year'] = self.data['foreword'][-4:]
        output['Home School Name'] =  self.data['school']['schoolName']
        for field in fields:
            if field not in output.columns:
                output[field] = ""
        output[fields].to_csv(csv_file, index=False)

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
