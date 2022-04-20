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
"""A requests.requests.Session class for accessing the Compass API."""

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


def current_ms_time() -> int:
    """Returns the current millisecond time."""
    return round(time.time() * 1000)


def sanitise_filename(filename):
    filename = re.sub(r'[/\\]+', '', filename)
    filename = re.sub(' +', ' ', filename)
    return filename


class CompassAuthenticator(Protocol):
    """An abstract class for generic Compass authenticators."""

    @abstractmethod
    def authenticate(self, session: CompassSession):
        raise NotImplementedError


class CompassFirefoxCookieAuthenticator(CompassAuthenticator):
    """A Compass authenaticator that gets login details from the local Firefox installation."""

    def authenticate(self, s: CompassSession):
        cj = browser_cookie3.firefox(
            domain_name=f'{s.school_code}.compass.education')

        for cookie in cj:
            c = {cookie.name: cookie.value}
            s.cookies.update(c)


class CompassAuthenticationError(Exception):
    """Authentication with Compass failed."""
    pass


class CompassConfigAuthenticator(CompassAuthenticator):
    """Authenticates using a provided username and password."""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def authenticate(self, s: CompassSession):
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        s.headers.update(headers)
        login_url = f"https://{s.school_code}.compass.education/login.aspx?sessionstate=disabled"
        # get viewstate
        r = s.get(login_url)
        pattern = 'id="__VIEWSTATE" value="(?P<viewstate>[0-9A-Za-z+/]*)"'
        m = re.search(pattern, r.text)
        viewstate = quote(m.group('viewstate'))
        pattern = 'id="__VIEWSTATEGENERATOR" value="(?P<viewstategenerator>[0-9A-Za-z+/]*)"'
        m = re.search(pattern, r.text)
        viewstategenerator = quote(m.group('viewstategenerator'))
        # url encode username and password
        username = quote(self.username)
        password = quote(self.password)
        # auth
        payload = f'__EVENTTARGET=button1&__EVENTARGUMENT=&__VIEWSTATE={viewstate}&browserFingerprint=3597254041&username={username}&password={password}&g-recaptcha-response=&rememberMeChk=on&__VIEWSTATEGENERATOR={viewstategenerator}'
        r = s.post(login_url, data=payload)
        if r.status_code != 200:
            raise CompassAuthenticationError


class CompassCLIAuthenticator(CompassAuthenticator):
    """Authenticates using login details from CLI prompt."""

    def authenticate(self, s: CompassSession):
        username = input("Compass username: ")
        password = input("Compass password: ")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        s.headers.update(headers)
        login_url = f"https://{s.school_code}.compass.education/login.aspx?sessionstate=disabled"
        # get viewstate
        r = s.get(login_url)
        pattern = 'id="__VIEWSTATE" value="(?P<viewstate>[0-9A-Za-z+/]*)"'
        m = re.search(pattern, r.text)
        viewstate = quote(m.group('viewstate'))
        pattern = 'id="__VIEWSTATEGENERATOR" value="(?P<viewstategenerator>[0-9A-Za-z+/]*)"'
        m = re.search(pattern, r.text)
        viewstategenerator = quote(m.group('viewstategenerator'))
        # url encode username and password
        username = quote(username)
        password = quote(password)
        # auth
        payload = f'__EVENTTARGET=button1&__EVENTARGUMENT=&__VIEWSTATE={viewstate}&browserFingerprint=3597254041&username={username}&password={password}&g-recaptcha-response=&rememberMeChk=on&__VIEWSTATEGENERATOR={viewstategenerator}'
        r = s.post(login_url, data=payload)
        if r.status_code != 200:
            raise CompassAuthenticationError


class CompassSession(requests.sessions.Session):
    """A requests Session extension with methods for accessing data from Compass."""

    def __init__(self, school_code: str, authenticator: CompassAuthenticator):
        """Creates a requests Session with Compass authentication completed.
        
        Args:
            school_code: Your school's compass school code.
            authenticator: An instance of CompassAuthenticator to perform the
                required authentication with Compass.
        """
        requests.sessions.Session.__init__(self)
        headers = {
            "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0"
        }
        self.headers.update(headers)
        self.school_code = school_code

        authenticator.authenticate(self)

    def long_running_file_request(self, request_payload: str,
                                  save_dir: str) -> str:
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.headers.update(headers)

        request_url = f"https://{self.school_code}.compass.education/Services/LongRunningFileRequest.svc/QueueTask"
        max_attempts = 5
        for i in range(max_attempts):
            r = self.post(request_url, data=request_payload)
            data = r.json()
            if 'd' in data:
                guid = data['d']
                break
            else:
                if i < max_attempts - 1:
                    time.sleep(5)
                    print(
                        f"File request error. Retrying {max_attempts - i - 1} more times."
                    )
                else:
                    print('File request failed.')
                    return ""
        # poll for status
        poll_url = f"https://{self.school_code}.compass.education/Services/LongRunningFileRequest.svc/PollTaskStatus"
        payload = {"guid": guid}
        r = self.post(poll_url, json=payload)
        data = r.json()
        status = data['d']['requestStatus']
        while status == 2:
            time.sleep(6)
            r = self.post(poll_url, json=payload)
            data = r.json()
            status = data['d']['requestStatus']
        if status != 3:
            raise ValueError("Unexpected Compass response.")
        # get file details
        get_task_url = f"https://{self.school_code}.compass.education/Services/LongRunningFileRequest.svc/GetTask"
        payload = {"guid": guid}
        r = self.post(get_task_url, json=payload)
        data = r.json()
        file_name = data['d']["filename"]
        file_id = data['d']["cdn_fileId"]
        # download the file
        file_download_url = f"https://{self.school_code}.compass.education/Services/FileDownload/FileRequestHandler?FileDownloadType=9&file={file_id}&fileName={file_name}".replace(
            " ", "%20")
        r = self.get(file_download_url)
        # save response
        save_path = os.path.join(save_dir, sanitise_filename(file_name))
        with open(save_path, "wb") as f:
            f.write(r.content)
        return save_path

    def export_progress_reports(self, cycle_id: int, cycle_title: str,
                                save_dir: str):
        payload = f'{{"type":"35","parameters":"{{\\"cycleId\\":{cycle_id},\\"cycleName\\":\\"{cycle_title}\\",\\"displayType\\":1}}"}}'
        self.long_running_file_request(payload, save_dir)

    def export_learning_tasks(self, academic_year_id: int,
                              academic_year_name: str, save_dir: str):
        payload = f'{{"type":"47","parameters":"{{\\"academicYearId\\":{academic_year_id},\\"academicYearName\\":\\"{academic_year_name}\\"}}"}}'
        self.long_running_file_request(payload, save_dir)

    def export_reports(self, cycle_id: int, cycle_year: int, cycle_title: str,
                       save_dir: str):
        payload = f'{{"type":"2","parameters":"{{\\"cycleId\\":{cycle_id}}}"}}'
        filename = self.long_running_file_request(payload, save_dir)
        head, tail = os.path.split(filename)
        sanitised_title = sanitise_filename(cycle_title)
        new_tail = f"SemesterReports-{cycle_year}-{sanitised_title}.csv"
        new_filename = os.path.join(head, new_tail)
        if os.path.exists(new_filename):
            os.remove(new_filename)
        os.rename(filename, new_filename)

    def get_report_cycles(self):
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.headers.update(headers)

        cycles_url = f"https://{self.school_code}.compass.education/Services/Reports.svc/GetCycles?_dc={current_ms_time()}"
        cycles = []
        page = 1
        payload = f'{{"page":{page},"start":{25*(page-1)},"limit":25}}'
        r = self.post(cycles_url, data=payload)
        new_cycles = r.json()['d']
        cycles += new_cycles
        while len(new_cycles) == 25:
            page += 1
            payload = f'{{"page":{page},"start":{25*(page-1)},"limit":25}}'
            r = self.post(cycles_url, data=payload)
            new_cycles = r.json()['d']
            cycles += new_cycles
        return cycles

    def get_progress_report_cycles(self):
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.headers.update(headers)

        cycles_url = f"https://{self.school_code}.compass.education/Services/Gpa.svc/GetCyclesForPagedGrid?sessionstate=readonly&_dc={current_ms_time()}"
        cycles = []
        page = 1
        payload = f'{{"page":{page},"start":{10*page-10},"limit":10}}'
        r = self.post(cycles_url, data=payload)
        decoded_response = r.json()['d']
        new_cycles = decoded_response['data']
        cycles += new_cycles
        while len(new_cycles) == 10:
            page += 1
            payload = f'{{"page":{page},"start":{10*(page-1)},"limit":10}}'
            r = self.post(cycles_url, data=payload)
            new_cycles = r.json()['d']['data']
            cycles += new_cycles
        return cycles

    def get_academic_groups(self):
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.headers.update(headers)

        learning_tasks_admin_url = f"https://{self.school_code}.compass.education/Communicate/LearningTasksAdministration.aspx"
        r = self.get(learning_tasks_admin_url)
        pattern = "Compass.referenceDataCacheKeys.schoolConfigKey = '(?P<key>[0-9a-z-]*)'"
        m = re.search(pattern, r.text)
        key = m.group('key')
        groups = []
        page = 1
        academic_groups_url = f"https://{self.school_code}.compass.education/Services/ReferenceDataCache.svc/GetAllAcademicGroups?sessionstate=readonly&v={key}&page={page}&start={25*(page-1)}&limit=25"
        r = self.get(academic_groups_url)
        new_groups = r.json()['d']
        groups += new_groups
        while len(new_groups) == 25:
            page += 1
            academic_groups_url = f"https://{self.school_code}.compass.education/Services/ReferenceDataCache.svc/GetAllAcademicGroups?sessionstate=readonly&v={key}&page={page}&start={25*(page-1)}&limit=25"
            r = self.get(academic_groups_url)
            new_groups = r.json()['d']
            groups += new_groups
        return groups

    def export_student_details(self,
                               file_name: str = "student details.csv",
                               detailed: bool = False) -> None:
        '''Exports student details from Compass.

        The basic export includes student codes, name, gender, year level and
        form group. It only includes current students.
        The detailed export also includes DOB, VCAA code, VSN, and school 
        house. It includes students who have exited.

        Args:
            file_name: The file path to save the csv export, including filename.
            detailed: Whether to perform a detailed student details export.
        '''
        if detailed:
            url = f"https://{self.school_code}.compass.education/Services/FileDownload/CsvRequestHandler?type=37"
        else:
            url = f"https://{self.school_code}.compass.education/Services/FileDownload/CsvRequestHandler?type=38"
        r = self.get(url)
        with open(file_name, "wb") as f:
            f.write(r.content)

    def export_student_household_information(
            self, file_name: str = "student household information.csv") -> None:
        '''Exports student household information from Compass.

        The basic export includes student address, parent names and parent contact details.

        Args:
            file_name: The file path to save the csv export, including filename.
        '''
        url = f"https://{self.school_code}.compass.education/Services/FileDownload/CsvRequestHandler?type=14"
        r = self.get(url)
        with open(file_name, "wb") as f:
            f.write(r.content)

    def export_sds(self,
                   save_dir: str = ".",
                   academic_group: int = -1,
                   append_date: bool = False):
        '''Exports class enrolment and teacher information from Compass.

        Downloads the Microsoft SDS export from Compass.
        
        Requires access to SDS Export rights in the Subjects and Classes page.

        Will save four files in the provided path:
            StudentEnrollment.csv: contains student->class mappings
            Teacher.csv: contains teacher id information
            TeacherRoster.csv: contains teacher->class mappings
            Section.csv: contains class id information

        Args:
            save_dir: The directory to save the export.
            academic_group: The academic group (e.g. the year) to download the export 
                for, defaults to the current active group.
            append_date: If True, append today's date to the filenames in
                yyyy-mm-dd format.
        '''
        payload = f'{{"type":"77","parameters":"{{\\"schoolSisId\\":\\"1\\",\\"studentSisId\\":1,\\"studentUsername\\":1,\\"teacherUsername\\":1,\\"sectionSisId\\":1,\\"sectionName\\":1,\\"academicGroup\\":{academic_group}}}"}}'
        archive_file_name = self.long_running_file_request(payload, save_dir)
        # unpack archive
        contents = [
            "StudentEnrollment.csv", "Teacher.csv", "TeacherRoster.csv",
            "Section.csv"
        ]
        with zipfile.ZipFile(archive_file_name, 'r') as zip_ref:
            for content in contents:
                if append_date:
                    today = datetime.today().strftime('%Y-%m-%d')
                    parts = content.split('.')
                    new_filename = parts[0] + " " + today + "." + parts[1]
                    info = zip_ref.getinfo(content)
                    info.filename = new_filename
                    zip_ref.extract(info, path=save_dir)
                else:
                    zip_ref.extract(content, path=save_dir)
        os.remove(archive_file_name)


def get_report_cycle_id(cycles, year, name):
    for c in cycles:
        if c['year'] == year and c['name'] == name:
            return c['id']
    return None
