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
"""Utilities for importing and exporting data into OARS."""

from __future__ import annotations

from abc import abstractmethod
from collections import abc
from datetime import datetime
from html.parser import HTMLParser
import json
import re
import requests
import time
from typing import Protocol

import browser_cookie3
import numpy as np
import pandas as pd

from vicedtools.acer import score_categoriser

# Todo: Transition from only adding maths/english class codes to adding all
# relevant class codes as tags from the student enrolment data


def class_selector(class_string: str) -> pd.Series:
    '''Identifies whether a given class name is an english or maths class.

    Args:
        class_string: a class code string

    Returns:
        A pandas Series containing two items, "Maths"/"English" and the class code.
    '''
    # maths pattern
    pattern = "(?P<class_code>[789]MA[BEFG][0-9]|10MA[PQRSTU][X]?[0-9]|11FM[PQRSTU][0-9])"
    match = re.match(pattern, class_string)
    if match:
        class_code = match.group("class_code")
        return pd.Series(["Maths", class_code])
    # english/eal pattern
    pattern = "(?P<class_code>[789]EN[BEFG][0-9]|10EN[PQRSTU][0-9]|[789]EAL[BEFG][0-9]?|10EAL[PQRSTU][0-9]?)"
    match = re.match(pattern, class_string)
    if match:
        class_code = match.group("class_code")
        return pd.Series(["English", class_code])
    # else
    return pd.Series([None, None])


def student_imports(student_details_file: str, student_enrolment_file: str,
                    current_students_file: str, new_students_file: str,
                    update_students_file: str) -> None:
    '''Creates files to update the OARS student database.

    Creates two separate files, one to update the details of existing students
    in the database and one to add new students.

    Args:
        student_details_file: a student details export csv from Compass. Can be 
            downloaded using vicedtools.compass.export_student_details or directly
            from https://[schoolID].compass.education/Services/FileDownload/CsvRequestHandler?type=37
        student_enrolment_file: a student enrolment file exported from Compass.
            Can be downloaded using vicedtools.compass.export_student_enrolments
        current_students_file: a current students export from OARS
        new_students_file: the filename to save the new students import for OARS
        update_students_file: the filename to save the update students import for OARS
    '''
    existing_students_df = pd.read_excel(current_students_file)
    student_details_df = pd.read_csv(student_details_file, dtype=np.str)
    student_enrolment_df = pd.read_csv(student_enrolment_file)

    # create new student details columns
    # columns needed
    # System ID, Family name, Given name, Middle names, Username, Password,
    # Date of birth, Gender Tags, Unique ID, Enrolled, Year level, School year
    student_details_df.rename(columns={
        "Last Name": "Family name",
        "Preferred Name": "Given name",
        "SUSSI ID": "Username",
        "Year Level": "Year level"
    },
                              inplace=True,
                              errors="raise")
    # column formatting
    student_details_df["Family name"] = student_details_df[
        "Family name"].str.title()
    student_details_df["Date of birth"] = pd.to_datetime(
        student_details_df["Date of birth"], format="%d/%m/%Y")
    student_details_df["Date of birth"] = student_details_df[
        "Date of birth"].dt.strftime("%d-%m-%Y")
    # select relevant columns
    columns = [
        "Family name", "Given name", "Username", "Date of birth", "Gender",
        "Year level", "Form Group"
    ]
    student_details_df = student_details_df[columns]
    # create other columns
    student_details_df["Middle names"] = ""
    student_details_df["Password"] = student_details_df["Date of birth"]
    student_details_df["Unique ID"] = student_details_df["Username"]
    student_details_df["School year"] = datetime.today().stftime('%Y')
    student_details_df["Enrolled"] = "Enrolled"

    student_enrolment_df[[
        "Subject", "Class code"
    ]] = student_enrolment_df["Section SIS ID"].apply(class_selector)
    student_enrolment_df.dropna(subset=["Subject"], inplace=True)
    # remove multiple enrolments (keep most recent)
    student_enrolment_df.drop_duplicates(subset=["SIS ID", "Subject"],
                                         keep="last",
                                         inplace=True)
    # pivot to create english and maths columns
    student_enrolment_df = student_enrolment_df.pivot(
        index="SIS ID", columns="Subject", values="Class code").reset_index()
    student_enrolment_df.rename(columns={"SIS ID": "Username"}, inplace=True)
    # merge with student details and create class tag string
    student_details_df = student_details_df.merge(student_enrolment_df,
                                                  on="Username")
    student_details_df["Tags"] = (student_details_df["Form Group"] + "," +
                                  student_details_df["English"] + "," +
                                  student_details_df["Maths"])

    # check existing list and unenrol exited students+
    #oars_df["Date of birth"] = pd.to_datetime(oars_df["Date of birth"])
    #oars_df["Password"] = oars_df["Date of birth"]
    students_to_unenrol = pd.DataFrame(
        existing_students_df[~existing_students_df["Username"].
                             isin(student_details_df["Username"])])
    students_to_unenrol["Enrolled"] = "Unenrolled"
    students_to_unenrol["Tags"] = ""

    student_details_df = student_details_df.merge(
        existing_students_df[["System ID", "Username"]],
        on="Username",
        how="left")
    student_details_df.fillna("", inplace=True)

    columns = [
        "System ID", "Family name", "Given name", "Middle names", "Username",
        "Password", "Date of birth", "Gender", "Tags", "Unique ID", "Enrolled",
        "Year level", "School year"
    ]
    export_df = pd.concat([student_details_df[columns], students_to_unenrol])
    export_df = export_df[columns]

    # separate exports for new students and updating existing students
    export_df[export_df["System ID"] != ""].to_excel(update_students_file,
                                                     index=False)
    new_student_columns = [
        "Family name", "Given name", "Middle names", "Username", "Password",
        "Date of birth", "Gender", "Tags", "Unique ID", "Year level",
        "School year"
    ]
    export_df[export_df["System ID"] == ""][new_student_columns].to_excel(
        new_students_file, "Sheet1", index=False)


class OARSAuthenticator(Protocol):
    """An abstract class for generic OARS authenticators."""

    @abstractmethod
    def authenticate(self, session: OARSSession):
        raise NotImplementedError


class OARSFirefoxCookieAuthenaticator(OARSAuthenticator):
    """An OARS authenaticator that gets login details from the local Firefox installation."""

    def authenticate(self, s: OARSSession):
        cj = browser_cookie3.firefox(domain_name='oars.acer.edu.au')

        for cookie in cj:
            c = {cookie.name: cookie.value}
            s.cookies.update(c)


class OARSAuthenticateError(Exception):
    """Raised if an error occurs related to OARS authentication."""
    pass


class TestNotFoundError(Exception):
    """Raised if an OARS test id or name is not found."""
    pass


class FormNotFoundError(Exception):
    """Raised if an OARS form id or name is not found."""
    pass


class SecurityTokenParser(HTMLParser):
    """Extracts the OARS security token from a page."""

    def handle_data(self, data):
        if 'oarsData' in data:
            data = json.loads(data[22:])
            self.security_token = data['securityToken']


class OARSSession(requests.sessions.Session):
    """A requests Session extension with methods for accessing data from OARS."""

    def __init__(self, school: str, authenticator: OARSAuthenticator):
        """Creates a requests Session with OARS authentication completed.
        
        Args:
            school: An OARS school string. E.g. https://oars.acer.edu.au/{your school string}/...
            authenticator: An instance of OARSAuthenticator.
            """
        requests.sessions.Session.__init__(self)
        headers = {
            "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0"
        }
        self.headers.update(headers)

        authenticator.authenticate(self)
        self.school = school
        r = self.get(f"https://oars.acer.edu.au/{school}/reports-new")
        parser = SecurityTokenParser()
        parser.feed(r.text)
        self.security_token = parser.security_token

        self._get_test_metadata()
        self._get_scale_constructs()

    def _get_test_metadata(self):
        """Downloads test metadata from OARS."""
        url = f"https://oars.acer.edu.au/api/{self.school}/reports-new/getTests/"
        r = self.get(url)
        try:
            self.tests = PATTests(r.json())
        except json.JSONDecodeError:
            raise OARSAuthenticateError()

    def _get_scale_constructs(self):
        """Downloads scale constructs from OARS."""
        self.scale_constructs = {}
        for test in self.tests:
            if 'scale_id' in test:
                scale_id = test['scale_id']
                url = f"https://oars.acer.edu.au/api/{self.school}/reports-new/getScaleConstruct?scale_id={scale_id}"
                r = self.get(url)
                try:
                    self.scale_constructs[scale_id] = r.json()
                except json.JSONDecodeError:
                    raise OARSAuthenticateError()

    def get_pat_results(self, test_name: str, form_name: str, from_date: str,
                        to_date: str) -> PATSittings:
        """Downloads the results for a single PAT test.
        
        Args:
            test_name: The name of the test. E.g. "PAT Maths 4th Edition"
            form_name: The form to download. E.g. "PAT Maths Test 6"
            from_date: The start date to download results for in 
                dd-mm-yyyy format.
            to_date: The end date to download results for in dd-mm-yyyy format.
            
        Returns:
            A list of test sittings.
        """
        test = self.tests.get_test_from_name(test_name)
        test_id = test["id"]
        form_id = test.get_form_id_from_name(form_name)
        scale_id = test["scale_id"]
        scale_slug = self.scale_constructs[scale_id]['slug']
        ids_url = f"https://oars.acer.edu.au/api/{self.school}/reports-new/getSittingIdsByTestForm/?scale_slug={scale_slug}&test_id={test_id}&form_id={form_id}&from={from_date}&to={to_date}&match_criterion=all&date-type=between&form_name={form_name}&test_name={test_name}&report_type=pat&tag_year_match_criterion=and&report_template=pat"
        ids_url = ids_url.replace(" ", "%20")

        r = self.get(ids_url)
        ids = r.json()

        sittings_url = f"https://oars.acer.edu.au/api/{self.school}/reports-new/getGroupReportSittingsByIds.ajax/?scale_slug={scale_slug}&test_id={test_id}&form_id={form_id}&from={from_date}&to={to_date}&match_criterion=all&date-type=between&form_name={form_name}&test_name={test_name}&report_type=pat&tag_year_match_criterion=and&report_template=pat"
        sittings_url = sittings_url.replace(" ", "%20")

        sittings = []
        for i in range(0, len(ids[test_id][form_id]), 100):
            payload = {
                'ids': ids[test_id][form_id][i:i + 100],
                'security_token': self.security_token
            }
            r = self.post(sittings_url, json=payload)
            sittings += r.json()
        return PATSittings(sittings)

    def get_all_pat_sittings(self, from_date: str, to_date: str) -> PATSittings:
        """Downloads the results for all PAT sittings between the given dates.
        
        Includes both PAT Maths 4th Edition and PAT Reading 5th Edition.
        
        Args:
            from_date: The start date to download results for in 
                dd-mm-yyyy format.
            to_date: The end date to download results for in dd-mm-yyyy format.
            
        Returns:
            A list of test sittings.
        """
        test_names = ["PAT Maths 4th Edition", "PAT Reading 5th Edition"]

        sittings = []

        for test_name in test_names:
            test = self.tests.get_test_from_name(test_name)
            test_id = test['testId']
            scale_id = test['scale_id']
            scale_slug = self.scale_constructs[scale_id]['slug']

            forms = test['forms']
            for form in forms:
                form_id = form['formId']
                form_name = form['name']

                ids_url = f"https://oars.acer.edu.au/api/{self.school}/reports-new/getSittingIdsByTestForm/?scale_slug={scale_slug}&test_id={test_id}&form_id={form_id}&from={from_date}&to={to_date}&match_criterion=all&date-type=between&form_name={form_name}&test_name={test_name}&report_type=pat&tag_year_match_criterion=and&report_template=pat"
                ids_url = ids_url.replace(" ", "%20")

                r = self.get(ids_url)
                ids = r.json()

                if ids:
                    sittings_url = f"https://oars.acer.edu.au/api/{self.school}/reports-new/getGroupReportSittingsByIds.ajax/?scale_slug={scale_slug}&test_id={test_id}&form_id={form_id}&from={from_date}&to={to_date}&match_criterion=all&date-type=between&form_name={form_name}&test_name={test_name}&report_type=pat&tag_year_match_criterion=and&report_template=pat"
                    sittings_url = sittings_url.replace(" ", "%20")

                    for i in range(0, len(ids[test_id][form_id]), 100):
                        payload = {
                            'ids': ids[test_id][form_id][i:i + 100],
                            'security_token': self.security_token
                        }
                        r = self.post(sittings_url, json=payload)
                        sittings += r.json()
        return PATSittings(sittings)

    def get_items(self, test_id: str, form_id: str,
                  sitting_id: str) -> PATItems:
        """Gets PAT Item metadata.
        
        Args:
            test_id: The id of the test to get item metadata for.
            form_id: The id of the form to get item metadata for.
            sitting_id: The sitting id for a sitting of this test form.
            
        Returns:
        """
        test = self.tests.get_test_from_id(test_id)
        test_name = test['name']
        scale_id = test['scale_id']
        scale_slug = self.scale_constructs[scale_id]['slug']
        form_name = test.get_form_name_from_id(form_id)
        from_date = '27-02-2022' # dates dont matter
        to_date = '27-02-2022'

        url = f"https://oars.acer.edu.au/api/{self.school}/reports-new/getGroupReportItemsData/?scale_slug={scale_slug}&test_id={test_id}&form_id={form_id}&from={from_date}&to={to_date}&match_criterion=all&date-type=between&form_name={form_name}&test_name={test_name}&report_type=pat&tag_year_match_criterion=and&report_template=pat"

        payload = {
            'ids': [sitting_id],
            'security_token': self.security_token,
            'sitting_id': [sitting_id],
            'sittingId': [sitting_id],
            'sittingIds': [sitting_id]
        }
        r = self.post(url, json=payload)

        return PATItems(r.json())

    def get_candidates(self, enrolled: int = 1) -> PATCandidates:
        """Gets candidate data.
        
        Args:
            enrolled: 0 for unenrolled students, 1 for enrolled students and
                2 for pre-enrolled students.
        
        Returns:
            An instance of PATCandidates.
        """

        ids_url = f"https://oars.acer.edu.au/api/{self.school}/candidates/getCandidateIds?enrolled={enrolled}"
        r = self.get(ids_url)
        ids = r.json()

        candidates = []
        if ids:
            candidates_url = f"https://oars.acer.edu.au/api/{self.school}/candidates/getCandidatesByIds/"
            for i in range(0, len(ids), 50):
                payload = {
                    'extraFields': ['password_visible'],
                    'ids': ids[i:i + 50],
                    'security_token': self.security_token,
                    'withForms': 'true'
                }
                r = self.post(candidates_url, json=payload)
                candidates += r.json()

        return PATCandidates(candidates)


def year_level_at_time_of_test(year_levels: dict, time_of_test: int) -> str:
    for yr in year_levels['history']:
        if time_of_test > yr['start']['sec'] and time_of_test < yr['end']['sec']:
            return yr['value']
    return ""


def extract_response(response: dict) -> str:
    if response['class'] == 'correct':
        return '✓'
    else:
        return response['key']


class PATTests(list):
    """A class for storing metadata for PAT Tests."""

    def __init__(self, tests: list[dict]):
        if isinstance(tests, PATTests):
            return tests
        if isinstance(tests, abc.Sequence):
            super().__init__([PATTest(i) for i in tests])
        else:
            raise TypeError(f"Unsupported type: {type(tests)}")

    def get_test_from_id(self, test_id: str) -> PATTest:
        """Gets a test's metadata.
        
        Args:
            test_id: The testId of the test to locate.
            
        Returns:
            A PATTest containing metadata about the particular test.
        """
        for t in self:
            if t['testId'] == test_id:
                return t
        raise TestNotFoundError()

    def get_test_from_name(self, test_name: str) -> PATTest:
        """Gets a test's metadata.
        
        Args:
            test_name: The name of the test to locate. 
                E.g. "PAT Maths 4th Edition"
            
        Returns:
            A PATTest containing metadata about the particular test
        """
        for t in self:
            if t['name'] == test_name:
                return t
        raise TestNotFoundError()

    def get_id_from_name(self, test_name: str) -> str:
        """Gets a test's id from its name.
        
        Args:
            test_name: The name of the test to locate. 
                E.g "PAT Maths 4th Edition"
            
        Returns:
            The id string for the test.
        """
        for t in self:
            if t['name'] == test_name:
                return t['testId']
        raise TestNotFoundError()

    def get_name_from_id(self, test_id: str) -> str:
        """Gets a test's name from its id.
        
        Args:
            test_id: The id of the test to locate. 
            
        Returns:
            The name ofr the test. E.g "PAT Maths 4th Edition"
        """
        for t in self:
            if t['id'] == test_id:
                return t['name']
        raise TestNotFoundError()


class PATTest(dict):
    """A class for storing metadata for a PAT Test"""

    def __init__(self, test):
        super().__init__(test)

    def get_form_id_from_name(self, form_name: str) -> str:
        """Gets a form's id from its name.
        
        Args:
            form_name: The name of the form. E.g. "PAT Maths Test 6"
            
        Returns:
            The id of the form.
        """
        for f in self['forms']:
            if f["name"] == form_name:
                return f["formId"]
        raise FormNotFoundError()

    def get_form_name_from_id(self, form_id: str) -> str:
        """Gets a form's name from it's id.
        
        Args:
            form_id: The id of the form
            
        Returns:
            The name of the form. E.g. "PAT Maths Test 6"
        """
        for f in self['forms']:
            if f["id"] == form_id:
                return f["name"]
        raise FormNotFoundError()


class PATSitting(dict):
    """A class for storing a PAT sitting result."""

    def group_report(self, tests: PATTests) -> dict:
        """Returns the data provided in a PAT group report export for this sitting."""
        data = {}
        try:
            data['Unique ID'] = self['unique_id']
        except KeyError:
            data['Unique ID'] = ""
        data['Family name'] = self['family_name']
        data['Given name'] = self['given_name']
        try:
            data['Middle names'] = self['middle_name']
        except KeyError:
            data['Middle names'] = ""
        data['Username'] = self['username']
        data['DOB'] = datetime.strptime(str(self['dob']), "%Y%m%d")
        data['Gender'] = self['gender'].title()
        data['Completed'] = datetime.strptime(
            time.ctime(self['sitting']['completed']), "%a %b %d %H:%M:%S %Y")
        data['Year level (current)'] = self['yearLevel']['current']
        data['Year level (at time of test)'] = year_level_at_time_of_test(
            self['yearLevel'], self['sitting']['updated'])
        data['Active tags'] = ""
        data['Inactive tags'] = ""
        for key, value in self['responses'].items():
            data[key] = extract_response(value)
        data['Score'] = self['score']['score']
        data['Scale'] = self['score']['scale']
        data['Score'] = self['score']['score']
        data['Stanine'] = self['score']['norms'][1]['stanine']
        data['Percentile'] = self['score']['norms'][1]['percentile']

        test_id = self['sitting']['test_id']
        form_id = self['sitting']['form_id']
        test_name = tests.get_name_from_id(test_id)
        form_name = tests.get_test_from_id(test_id).get_form_name_from_id(
            form_id)
        data['Test'] = test_name
        data['Test form'] = form_name

        return data

    def summary(self, tests: PATTests) -> dict:
        """Extracts a summary of the results.
        
        Args:
            tests: An instance of PATTests containing the relevant test metadata.
        
        Returns:
            A dictionary containing the summary.
        """
        test_name_stub = {"PAT Maths 4th Edition": "Maths",
                          "PAT Reading 5th Edition": "Reading",
                          "PAT Maths Adaptive": "Maths",
                          "PAT Reading Adaptive": "Reading",
                          "eWrite": "eWrite"}

        test_id = self['sitting']['test_id']
        form_id = self['sitting']['form_id']
        test = tests.get_test_from_id(test_id)
        test_name = test['name']
        form_name = test.get_form_name_from_id(form_id)

        data = {}
        data['Username'] = self['username']
        data['Completed'] = datetime.strptime(
            time.ctime(self['sitting']['completed']), "%a %b %d %H:%M:%S %Y")
        data['Year level (at time of test)'] = "Year " + year_level_at_time_of_test(
                self['yearLevel'], self['sitting']['updated'])
        data['Test'] = test_name_stub[test_name]
        data['Test form'] = form_name
        data['Scale'] = self['score']['scale']
        data['Score category'] = score_categoriser(data['Test'], data['Year level (at time of test)'], data['Completed'], data['Scale'])

        return data

class PATSittings(list):
    """A class for storing PAT sitting results."""

    def __init__(self, sittings: list[dict]):
        if isinstance(sittings, PATSittings):
            return sittings
        if isinstance(sittings, abc.Sequence):
            super().__init__([PATSitting(i) for i in sittings])
        else:
            raise TypeError(f"Unsupported type: {type(sittings)}")

    def group_report(self, tests: PATTests, test_name: str, form_name: str) -> list:
        """Extracts data for the preparation of a group report spreadsheet.
        
        Args:
            tests: A PATTests instance containing the relevant test metadata.
            test_name: The name of the test to export. E.g. "PAT Maths 4th Edition"
            form_name: The name of the form to export. E.g. "PAT Maths Test 6"
            
        Returns:
            A list of dictionaries containing the relevant columns for each sitting.
        """
        test_id = tests.get_id_from_name(test_name)
        form_id = tests.get_test_from_name(test_name).get_form_id_from_name(
            form_name)
        data = []
        for sitting in self:
            if sitting["sitting"]["test_id"] == test_id and sitting["sitting"][
                    "form_id"] == form_id:
                data.append(sitting.group_report(tests))
        return data

    def summary(self, tests: PATTests, recent_only: bool = False) -> pd.DataFrame:
        """Extracts a basic summary of results.
        
        Args:
            tests: A PATTests instance containing the relevant test metadata.
            recent_only: If True, only give the most recent result for each student.
        
        Returns:
            A pandas DataFrame with the summary.
        """
        rows = [s.summary(tests) for s in self]
        df = pd.DataFrame.from_records(rows)
        if recent_only:
            df.sort_values("Completed", ascending=False, inplace=True)
            df.drop_duplicates(subset=["Username", "Test"], inplace=True)
        return df

class PATItems(list):
    """A class for storing metadata for PAT items."""

    def __init__(self, items: list[dict]):
        if isinstance(items, PATItems):
            return items
        if isinstance(items, abc.Sequence):
            super().__init__([PATItem(i) for i in items])
        else:
            raise TypeError(f"Unsupported type: {type(items)}")

    def group_report_key(self):
        """Returns data for the group report for this test."""
        data = [x.group_report_key() for x in self]
        return data


class PATItem(dict):
    """A class for storing metadata for a PAT item."""

    def __init__(self, item):
        super().__init__(item)

    def group_report_key(self):
        """Returns data for the group report key for this item."""
        data = {}
        data['Question number'] = self['position']
        data['Percentage correct'] = 0
        data['Strand'] = self['classification']
        data['Question difficulty'] = self['difficulty']
        return data


class PATCandidates(list):
    """A class for storing metadata for PAT candidates."""

    def __init__(self, candidates: list[dict]):
        if isinstance(candidates, PATCandidates):
            return candidates
        if isinstance(candidates, abc.Sequence):
            super().__init__([PATCandidate(i) for i in candidates])
        else:
            raise TypeError(f"Unsupported type: {type(candidates)}")

    def student_details_export(self,
                               include_sittings: bool = False) -> pd.DataFrame:
        """Extracts the student details data export from the candidates.
        
        Columns match the export provided by OARS.
        
        Args:
            include_tests: If true, adds an additional column listing any incomplete sittings.
        
        Returns:
            A pandas DataFrame with the student details table.
        """
        rows = [c.student_details_export(include_sittings) for c in self]
        data = pd.DataFrame.from_records(rows)
        return data

    def sitting_status_export(self) -> pd.DataFrame:
        """Extracts the sitting information from the candiates.
        
        Provides the completion status of all assigned sittings.
        
        Returns:
            A pandas DataFrame with the sitting details.
        """
        rows = []
        for sitting in self:
            rows += sitting.get_sitting_status()
        data = pd.DataFrame.from_records(rows)
        return data


class PATCandidate(dict):
    """A class for storing metadata for a PAT candidate."""

    def __init__(self, item):
        super().__init__(item)

    def student_details_export(self, include_sittings: bool = False):
        row = {}
        row["System ID"] = self['id']
        row["Family name"] = self['family_name']
        row["Given name"] = self['given_name']
        try:
            row["Middle names"] = self['middle_name']
        except KeyError:
            row["Middle names"] = ""
        row["Username"] = self['username']
        row["Password"] = self['plaintext_password']
        row["Date of birth"] = self['dobString']
        row["Gender"] = self['gender'].title()
        row["Tags"] = ",".join([t['name'] for t in self['tags']])
        row['Unique ID'] = self['unique_id']
        if self["enrolled"] == 1:
            row["Enrolled"] = 'enrolled'
        elif self['enrolled'] == 0:
            row["Enrolled"] = 'unenrolled'
        else:
            row['enrolled'] = 'pre-enrolled'
        row["Year level"] = self['year']
        row["School year"] = self['currentSchoolYearLabel']
        if include_sittings:
            incomplete = []
            for sitting in self['sittings']:
                if not sitting["completed"]:
                    incomplete.append(
                        f"{sitting['test_name']} {sitting['form_name']}")
            row["Incomplete tests"] = ",".join(incomplete)
        return row

    def get_sitting_status(self):
        rows = []
        for sitting in self['sittings']:
            row = {}
            row["System ID"] = self['id']
            row["Family name"] = self['family_name']
            row["Given name"] = self['given_name']
            row["Username"] = self['username']
            row["Tests"] = sitting['test_name']
            row["Form"] = sitting['form_name']
            row["Assigned date"] = datetime.strptime(
                time.ctime(sitting['created']),
                "%a %b %d %H:%M:%S %Y").strftime("%d-%m-%Y")
            if sitting["completed"]:
                row["Status"] = "Completed"
                row["Completed date"] = datetime.strptime(
                    time.ctime(sitting['created']),
                    "%a %b %d %H:%M:%S %Y").strftime("%d-%m-%Y")
            else:
                row["Status"] = "Incomplete"
                row["Completed date"] = ""
            rows.append(row)
        return rows
