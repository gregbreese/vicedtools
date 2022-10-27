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
"""A requests.requests.Session class for accessing the OARS API."""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from html.parser import HTMLParser
import json
import re
import requests
import time
from typing import Protocol
from urllib.parse import quote

import pandas as pd

import browser_cookie3

from vicedtools.acer.ewritesittings import EWriteSittings
from vicedtools.acer.oarscandidates import OARSCandidates
from vicedtools.acer.patitems import PATItems
from vicedtools.acer.patsittings import PATSittings
from vicedtools.acer.oarstests import OARSTests


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

        self.school = school
        authenticator.authenticate(self)
        r = self.get(f"https://oars.acer.edu.au/{school}/reports-new")
        pattern = r'"securityToken":"(?P<token>[\$0-9A-Za-z+/\.\\]*)"'
        m = re.search(pattern, r.text)
        self.security_token = m.group('token').replace('\\/','/')

        self._get_test_metadata()
        self._get_scale_constructs()

    def _get_test_metadata(self):
        """Downloads test metadata from OARS."""
        url = f"https://oars.acer.edu.au/api/{self.school}/reports-new/getTests/"
        r = self.get(url)
        try:
            self.tests = OARSTests(r.json())
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
        test_names = ["PAT Maths 4th Edition", 
                      "PAT Reading 5th Edition"]

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

                self.headers.update(
                    {"Content-Type": "application/json;charset=utf-8"})

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

                del self.headers["Content-Type"]
        return PATSittings(sittings)

    def updated_get_all_pat_sittings(self, from_date: str, to_date: str) -> PATSittings:
        """Downloads the results for all PAT sittings between the given dates.
                
        Args:
            from_date: The start date to download results for in 
                dd-mm-yyyy format.
            to_date: The end date to download results for in dd-mm-yyyy format.
            
        Returns:
            A list of test sittings.
        """
        test_names = ["PAT Maths 4th Edition", 
                      "PAT Reading 5th Edition",
                      "PAT Maths Adaptive",
                      "PAT Reading Adaptive"]

        test_names = []
        for t in self.tests:
            if t['reportType'] == "Pat":
                test_names.append(t['name'])

        sittings = []
        responses = []


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

                self.headers.update(
                    {"Content-Type": "application/json;charset=utf-8"})

                if ids:
                    sittings_url = f"https://oars.acer.edu.au/api/{self.school}/reports-new/getScaleReportSittingsByIds.ajax?scale_slug={scale_slug}&test_id={test_id}&form_id={form_id}&extra_candidate_fields=true&include_sitting_responses=true"
                    sittings_url = sittings_url.replace(" ", "%20")

                    for i in range(0, len(ids[test_id][form_id]), 100):
                        payload = {
                            'ids': ids[test_id][form_id][i:i + 100],
                            'security_token': self.security_token
                        }
                        r = self.post(sittings_url, json=payload)
                        sittings += r.json()

                    responses_url = f"https://oars.acer.edu.au/api/{self.school}/reports-new/getSittingResponses.ajax?scale_slug={scale_slug}&test_id={test_id}&form_id={form_id}"
                    responses_url = sittings_url.replace(" ", "%20")

                    for i in range(0, len(ids[test_id][form_id]), 100):
                        payload = {
                            'ids': ids[test_id][form_id][i:i + 100],
                            'security_token': self.security_token
                        }
                        r = self.post(responses_url, json=payload)
                        responses += r.json()

                del self.headers["Content-Type"]
        return PATSittings2(sittings, responses)        

    def get_ewrite_sittings(self, candidates: OARSCandidates, from_date: str,
                            to_date: str) -> EWriteSittings:
        """Downloads the results for eWrite sittings for the candidates.

        Downloads results between to_date and from_date.
        
        Args:
            candidates: A OARSCandidates instance with the candidates to get
                results for.
            from_date: The start date to download results for in 
                dd-mm-yyyy format.
            to_date: The end date to download results for in dd-mm-yyyy format.
            
        Returns:
            A list of test sittings.
        """
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.headers.update(headers)
        # get sitting ids from candidates
        from_date = datetime.strptime(from_date, "%d-%m-%Y")
        to_date = datetime.strptime(to_date, "%d-%m-%Y")

        test = self.tests.get_test_from_name('eWrite')
        test_id = test['id']
        sitting_ids = {}
        for f in test['forms']:
            sitting_ids[f['id']] = []

        for candidate in candidates:
            for sitting in candidate['sittings']:
                if sitting['test_id'] == test_id and 'completed' in sitting:
                    completed_date = datetime.strptime(
                        time.ctime(sitting['completed']),
                        "%a %b %d %H:%M:%S %Y")
                    if completed_date >= from_date and completed_date <= to_date:
                        sitting_ids[sitting['form_id']].append(sitting['id'])

        # download sitting data
        sittings = []
        for form_id, ids in sitting_ids.items():
            if ids:
                sittings_url = f"https://oars.acer.edu.au/api/{self.school}/survey-reports/getSurveyReportSittingsByIds.ajax?form_id={form_id}&test_id={test_id}"

                for i in range(0, len(ids), 100):
                    payload = {'ids': ids[i:i + 100]}
                    r = self.post(sittings_url, json=payload)
                    sittings += list(r.json()['sittings'].values())

        return EWriteSittings(sittings)

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
        from_date = '27-02-2022'  # dates dont matter
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

    def get_all_items(self, tests: OARSTests) -> pd.DataFrame:
        items = []
        for test in tests:
            for form in test['forms']:
                test_id = test['id']
                test_name = test['name']
                form_id = form['id']
                form_name = form['name']

                url = f"https://oars.acer.edu.au/api/{self.school}/survey-reports/getItems?test_id={test_id}&form_id={form_id}&limitFields[]=metadata"
                r = self.post(url)

                form_items = r.json()['itemSet']
                for i in form_items:
                    i.pop('metadata')
                temp_df = pd.DataFrame.from_records(form_items)
                temp_df['test_name'] = test_name
                temp_df['form_name'] = form_name
                temp_df['test_id'] = test_id
                temp_df['form_id'] = form_id
                items.append(temp_df)
        items_df = pd.concat(items)
        return items_df

    def get_candidates(self, enrolled: int = 1) -> OARSCandidates:
        """Gets candidate data.
        
        Args:
            enrolled: 0 for unenrolled students, 1 for enrolled students and
                2 for pre-enrolled students.
        
        Returns:
            An instance of OARSCandidates.
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

        return OARSCandidates(candidates)

    def get_staff_xlsx(self, xlsx_filename):
        """Downloads a XLSX of all staff details.
        
        Downloads the XLSX that is provided through the bulk edit staff
        interface.
        """
        staff_excel_export_url = f"https://oars.acer.edu.au/api/{self.school}/staff/exportExcel"
        payload = {
            'export_name': f"{self.school}-staff",
            'security_token': self.security_token
        }
        r = self.post(staff_excel_export_url, data=payload)
        response_filename = r.json()['filename']

        quoted_security_token = quote(self.security_token)
        download_url = f"https://oars.acer.edu.au/api/{self.school}/clients/downloadFile?filePath={response_filename}&security%5Btoken%5D={quoted_security_token}"
        r = self.get(download_url)
        with open(xlsx_filename, "wb") as f:
            f.write(r.content)

    def update_staff(self, staff_xlsx: str) -> bool:
        """Uploads a staff details to OARS.
        
        Args:
            staff_xlsx: The path to a correctly formatted XLSX with staff
                details.

        Returns:
            True if the upload was successful.
        """
        del self.headers['Content-Type']

        upload_url = f"https://oars.acer.edu.au/api/{s.school}/staff/bulkUpdate"
        files = {'upload': open(staff_xlsx, 'rb')}
        payload = {'security_token': self.security_token}
        r = self.post(upload_url, files=files, data=payload)
        return r.status_code == 200


class SecurityTokenParser(HTMLParser):
    """Extracts the OARS security token from a page."""

    def handle_data(self, data):
        if 'oarsData' in data:
            data = json.loads(data[22:])
            self.security_token = data['securityToken']


class OARSAuthenticator(Protocol):
    """An abstract class for generic OARS authenticators."""

    @abstractmethod
    def authenticate(self, session: OARSSession):
        raise NotImplementedError


class OARSFirefoxCookieAuthenticator(OARSAuthenticator):
    """An OARS authenticator that gets login details from the local Firefox installation."""

    def authenticate(self, s: OARSSession):
        cj = browser_cookie3.firefox(domain_name='oars.acer.edu.au')

        for cookie in cj:
            c = {cookie.name: cookie.value}
            s.cookies.update(c)


class OARSBasicAuthenticator(OARSAuthenticator):
    """Authenticates using a provided username and password."""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def authenticate(self, s: OARSSession):

        login_url = f"https://oars.acer.edu.au/{s.school}"
        # get security token
        r = s.get(login_url)
        pattern = r'name="security\[token\]" value="(?P<token>[\$0-9A-Za-z+/\.\\]*)"'
        m = re.search(pattern, r.text)
        security_token = quote(m.group('token'))
        # url encode username and password
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        s.headers.update(headers)
        username = quote(self.username)
        password = quote(self.password)
        # auth
        payload = f'security%5Btoken%5D={security_token}&username={username}&password={password}'
        r = s.post(login_url, data=payload)
        if r.status_code != 200:
            raise OARSAuthenticateError


class OARSAuthenticateError(Exception):
    """Raised if an error occurs related to OARS authentication."""
    pass
