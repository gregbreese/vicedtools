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
"""A requests.requests.Session class for accessing the VCAA data service."""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from math import ceil
import os
import re
import requests
import time
from typing import Protocol
from urllib.parse import quote
import zipfile

import browser_cookie3


class DataserviceAuthenticator(Protocol):
    """An abstract class for generic Data Service authenticators."""

    @abstractmethod
    def authenticate(self, session: DataserviceSession):
        raise NotImplementedError


class DataserviceAuthenticationError(Exception):
    """Authentication with Data Service failed."""
    pass


class CompassConfigAuthenticator(DataserviceAuthenticator):
    """Authenticates using a provided username and password."""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def authenticate(self, s: DataserviceSession):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        s.headers.update(headers)
        login_url = f"https://dataservice.vcaa.vic.edu.au/Account/Login?ReturnUrl=%2F"
        # get viewstate
        r = s.get(login_url)
        pattern = 'name="__RequestVerificationToken" type="hidden" value="(?P<token>[0-9A-Za-z-_+/]*)"'
        m = re.search(pattern, r.text)
        token = quote(m.group('token'))
        # url encode username and password
        username = quote(self.username)
        password = quote(self.password)
        # auth
        payload = f'__RequestVerificationToken={token}&UserName={username}&Password={password}'
        r = s.post(login_url, data=payload)
        if r.status_code != 200:
            raise DataserviceAuthenticationError


class DataserviceSession(requests.sessions.Session):
    """A requests Session extension with methods for accessing data from the VCAA data service."""

    def __init__(self, authenticator: DataserviceAuthenticator):
        """Creates a requests Session with Data Service authentication completed.
        
        Args:
            authenticator: An instance of DataserviceAuthenticator to perform the
                required authentication.
        """
        requests.sessions.Session.__init__(self)
        headers = {
            "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0"
        }
        self.headers.update(headers)

        authenticator.authenticate(self)

    def get_naplan_years(self):
        url = "https://dataservice.vcaa.vic.edu.au/DataExtract/Index"
        r = self.get(url)

        pattern = '''<select class="form-control" id="ReportingYearSelected_DataExtract" name="ReportingYearSelected_DataExtract">
                            (<option value="[0-9]{4}">[0-9]{4}</option>)+
                    </select>'''
        m = re.search(pattern, r.text)

    def export_naplan(self, year: str, save_dir: str):
        """Downloads the outcome and question results for NAPLAN.

        Prepends the year to the filenames.
        Currently only downloads Year 7 and Year 9.
        
        Args:
            year: The test year to download.encoding=
            save_dir: The folder to save the exports in.
        """
        url = f'https://dataservice.vcaa.vic.edu.au/DataExtract/GetZip?ReportingYear={year}&YearLevel=7,9,0&Outcome=0&OutcomeLevelSelectionsJson=[%22100%22,%22200%22,%22300%22,%22400%22,%22500%22,%22600%22,%22700%22,%22800%22,%22900%22,%221000%22]&QuestionLevelSelectionsJson=[%22101%22,%22102%22,%22103%22,%22104%22,%22105%22,%22106%22,%22107%22,%22108%22,%22109%22,%22110%22]&NationalDataJson=null&StateDataJson=null&SchoolDataJson=null&SchoolFileJson=null'
        r = self.get(url)

        temp_zip = os.path.join(save_dir, "NAPLAN extract.zip")
        with open(temp_zip, "wb") as f:
            f.write(r.content)
        contents = [
            "StudentOutcomeLevel_Yr7.csv", "StudentOutcomeLevel_Yr9.csv",
            "StudentQuestionLevel_Yr7.csv", "StudentQuestionLevel_Yr9.csv"
        ]
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            for content in contents:
                parts = content.split('.')
                new_filename = f"{year} {parts[0]}.{parts[1]}"
                info = zip_ref.get_info(content)
                info.filename = new_filename
                zip_ref.extract(new_filename, path=save_dir)
        os.remove(temp_zip)

    def export_sssr(self, year: str, save_dir: str):
        # get school code
        url = 'https://dataservice.vcaa.vic.edu.au/SSSRDownload/Index'
        r = self.get(url)
        pattern = 'name="SchoolSelected"><option value="(?P<schoolid>[0-9]*)">'
        m = re.search(pattern, r.text)
        schoolid = quote(m.group('schoolid'))
        # get SSSR
        url = f"https://dataservice.vcaa.vic.edu.au/SSSRDownload/SSSRDownload?year={year}&schoolCd={schoolid}"
        r = self.get(url)
        zip_file = os.path.join(save_dir, f"{year} NAPLAN SSSR.zip")
        with open(zip_file, "wb") as f:
            f.write(r.content)
