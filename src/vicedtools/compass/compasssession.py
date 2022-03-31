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
"""A requests.requests.Session calss for accessing the Compass API."""

from __future__ import annotations

from abc import abstractmethod
import os
import requests
import time
from typing import Protocol

import browser_cookie3


def current_ms_time() -> int:
    """Returns the current millisecond time."""
    return round(time.time() * 1000)


class CompassAuthenticator(Protocol):
    """An abstract class for generic Compass authenticators."""

    @abstractmethod
    def authenticate(self, session: CompassSession):
        raise NotImplementedError


class CompassFirefoxCookieAuthenaticator(CompassAuthenticator):
    """A Compass authenaticator that gets login details from the local Firefox installation."""

    def authenticate(self, s: CompassSession):
        cj = browser_cookie3.firefox(
            domain_name=f'{s.school_code}.compass.education')

        for cookie in cj:
            c = {cookie.name: cookie.value}
            s.cookies.update(c)


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
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
            'Content-Type':
                'application/json; charset=utf-8'
        }
        self.headers.update(headers)

        authenticator.authenticate(self)
        self.school_code = school_code

    def long_running_file_request(self, request_payload: str, save_dir: str):
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.headers.update(headers)

        request_url = f"https://{self.school_code}.compass.education/Services/LongRunningFileRequest.svc/QueueTask"
        r = self.post(request_url, data=request_payload)
        data = r.json()
        if 'd' in data:
            guid = data['d']
        else:
            raise ValueError("Unexpected Compass response.")
        # poll for status
        poll_url = f"https://{self.school_code}.education/Services/LongRunningFileRequest.svc/PollTaskStatus"
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
        save_path = os.path.join(save_dir, file_name)
        with open(save_path, "wb") as f:
            f.write(r.content)

    def export_progress_reports(self, cycle_id: int, cycle_name: str,
                                save_dir: str):
        payload = f'{{"type":"35","parameters":"{{\\"cycleId\\":{cycle_id},\\"cycleName\\":\\"{cycle_name}\\",\\"displayType\\":1}}"}}'
        self.long_running_file_request(payload, save_dir)

    def export_learning_tasks(self, academic_year_id: int,
                              academic_year_name: str, save_dir: str):
        payload = f'{{"type":"47","parameters":"{{\\"academicYearId\\":{academic_year_id},\\"academicYearName\\":\\"{academic_year_name}\\"}}"}}'
        self.long_running_file_request(payload, save_dir)

    def export_reports(self, cycle_id: int, save_dir: str):
        payload = f'{{"type":"2","parameters":"{{\\"cycleId\\":{cycle_id}}}"}}'
        self.long_running_file_request(payload, save_dir)

    def get_report_cycles(self):
        cycles_url = f"https://{self.school_code}.compass.education/Services/Reports.svc/GetCycles?_dc={current_ms_time()}"
        cycles = []
        page = 1
        payload = f'{"page":{page},"start":{25*(page-1)},"limit":25}'
        r = self.post(cycles_url, data=payload)
        new_cycles = r.json()['d']
        cycles += new_cycles
        while len(new_cycles) == 25:
            page += 1
            payload = f'{"page":{page},"start":{25*(page-1)},"limit":25}'
            r = self.post(cycles_url, data=payload)
            new_cycles = r.json()['d']
            cycles += new_cycles
        return cycles

    def get_progress_report_cycles(self):
        cycles_url = f"https:/{self.school_code}.compass.education/Services/Gpa.svc/GetCyclesForPagedGrid?sessionstate=readonly&_dc={current_ms_time()}"
        cycles = []
        page = 1
        payload = f'{"page":{page},"start":{10*(page-1)},"limit":10}'
        r = self.post(cycles_url, data=payload)
        new_cycles = r.json()['d']
        cycles += new_cycles
        while len(new_cycles) == 10:
            page += 1
            payload = f'{"page":{page},"start":{10*(page-1)},"limit":10}'
            r = self.post(cycles_url, data=payload)
            new_cycles = r.json()['d']
            cycles += new_cycles
        return cycles

    def get_academic_groups(self):
        learning_tasks_admin_url = f"https://{self.school_code}.compass.education/Communicate/LearningTasksAdministration.aspx"
        r = self.get(learning_tasks_admin_url)
        pattern = "Compass.referenceDataCacheKeys.schoolConfigKey = '(?P<key>)'"
        m = re.search(pattern, r.content)
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
