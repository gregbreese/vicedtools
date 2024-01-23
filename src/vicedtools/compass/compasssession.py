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

from datetime import datetime
from math import ceil
import os
import re
import requests
import time
import zipfile

from cloudscraper import CloudScraper
from vicedtools.compass import CompassAuthenticator

# Minimum interval between requests
MIN_REQUEST_INTERVAL = 500000000  # 500 milliseconds in nanoseconds
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"

def current_ms_time() -> int:
    """Returns the current millisecond time."""
    return round(time.time() * 1000)


def sanitise_filename(filename):
    filename = re.sub(r'[/\\:\*\?<>|]+', '', filename)
    filename = re.sub(' +', ' ', filename)
    return filename


class CompassLongRunningFileRequestError(Exception):
    """Long running file request failed."""
    pass


class CompassSession(CloudScraper):
    """A requests Session extension with methods for accessing data from Compass."""

    def __init__(self, school_code: str, authenticator: CompassAuthenticator):
        """Creates a requests Session with Compass authentication completed.
        
        Args:
            school_code: Your school's compass school code.
            authenticator: An instance of CompassAuthenticator to perform the
                required authentication with Compass.
        """
        CloudScraper.__init__(self)
        self.school_code = school_code

        self.last_request_time = 0

        authenticator.authenticate(self)
        self.MAX_POLL_REQUESTS = 100

    def get(self, *args, **kwargs):
        """Enforce a minimum delay between requests."""
        now = time.time_ns()
        wait_time = MIN_REQUEST_INTERVAL - now + self.last_request_time
        if wait_time > 0:
            time.sleep(wait_time / 1000000000)
        self.last_request_time = time.time_ns()
        return super().get(*args, **kwargs)

    def post(self, *args, **kwargs):
        """Enforce a minimum delay between requests."""
        now = time.time_ns()
        wait_time = MIN_REQUEST_INTERVAL - now + self.last_request_time
        if wait_time > 0:
            time.sleep(wait_time / 1000000000)
        self.last_request_time = time.time_ns()
        return super().post(*args, **kwargs)

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
                    print(r.text)
                else:
                    print('File request failed.')
                    return ""
        # poll for status
        time.sleep(1)
        poll_requests = 1
        poll_url = f"https://{self.school_code}.compass.education/Services/LongRunningFileRequest.svc/PollTaskStatus"
        payload = {"guid": guid}
        r = self.post(poll_url, json=payload)
        data = r.json()
        status = data['d']['requestStatus']
        while status <= 2:
            time.sleep(6)
            r = self.post(poll_url, json=payload)
            data = r.json()
            status = data['d']['requestStatus']
            poll_requests += 1
            if poll_requests > self.MAX_POLL_REQUESTS:
                break
        if status != 3:
            raise CompassLongRunningFileRequestError(
                f"Unexpected Compass response, after {poll_requests} poll requests received status: {status}"
            )
        # get file details
        get_task_url = f"https://{self.school_code}.compass.education/Services/LongRunningFileRequest.svc/GetTask"
        payload = {"guid": guid}
        r = self.post(get_task_url, json=payload)
        data = r.json()
        file_name = data['d']["filename"]
        file_id = data['d']["cdn_fileId"]
        # download the file
        del self.headers['Content-Type']
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
        """Exports a single progress report cycle.
        
        Args:
            cycle_id: The Compass cycle id for the cycle to download.
            cycle_title: The title of the cycle to download.
            save_dir: The folder to save the export into.
        """
        payload = f'{{"type":"35","parameters":"{{\\"cycleId\\":{cycle_id},\\"cycleName\\":\\"{cycle_title}\\",\\"displayType\\":1}}"}}'
        self.long_running_file_request(payload, save_dir)

    def export_learning_tasks(self, academic_year_id: int,
                              academic_year_name: str, save_dir: str):
        """Exports learning task data for a single academic group (cycle).
        
        Args:
            academic_year_id: The id for the academic group to download.
            academic_year_name: The title of the academic group to download.
            save_dir: The folder to save the export into.
        """
        payload = f'{{"type":"47","parameters":"{{\\"academicYearId\\":{academic_year_id},\\"academicYearName\\":\\"{academic_year_name}\\"}}"}}'
        self.long_running_file_request(payload, save_dir)

    def export_reports(self, cycle_id: int, cycle_year: int, cycle_title: str,
                       save_dir: str):
        """Exports a single  report cycle.
        
        Args:
            cycle_id: The Compass cycle id for the cycle to download.
            cycle_title: The title of the cycle to download.
            save_dir: The folder to save the export into.
        """
        payload = f'{{"type":"2","parameters":"{{\\"cycleId\\":{cycle_id}}}"}}'
        filename = self.long_running_file_request(payload, save_dir)
        head, _tail = os.path.split(filename)
        sanitised_title = sanitise_filename(cycle_title)
        new_tail = f"SemesterReports-{cycle_year}-{sanitised_title}.csv"
        new_filename = os.path.join(head, new_tail)
        if os.path.exists(new_filename):
            os.remove(new_filename)
        os.rename(filename, new_filename)

    def get_report_cycles(self) -> list[dict]:
        """Downloads metadata for Compass report cycles.
        
        Returns:
            A list of the metadata for each report cycle.
        """
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

    def get_progress_report_cycles(self) -> list[dict]:
        """Downloads metadata for progress report cycles.
        
        Returns:
            A list of the metadata for each progress report cycle.
        """
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

    def get_academic_groups(self) -> list[dict]:
        """Downloads academic group metadata from Compass.
        
        Returns:
            A list containing the metadata for each academic group.
        """
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.headers.update(headers)

        learning_tasks_admin_url = f"https://{self.school_code}.compass.education/Learn/Subjects.aspx"
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
            if new_groups[0]['id'] != 25 * (page - 1):
                break
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

    def export_student_custom_flags(self,
                                    file_name: str = "student custom flags.csv"
                                   ) -> None:
        '''Exports student flags that have been added to Compass.

        Note: Doesn't include flags imported through CASES.

        Args:
            file_name: The file path to save the csv export, including filename.
        '''
        url = f"https://{self.school_code}.compass.education/Services/FileDownload/CsvRequestHandler?type=17"
        r = self.get(url)
        with open(file_name, "wb") as f:
            f.write(r.content)

    def export_student_demographic_details(
            self, file_name: str = "student custom flags.csv") -> None:
        '''Exports student demographic details.

        Args:
            file_name: The file path to save the csv export, including filename.
        '''
        url = f"https://{self.school_code}.compass.education/Services/FileDownload/CsvRequestHandler?type=54"
        r = self.get(url)
        with open(file_name, "wb") as f:
            f.write(r.content)

    def export_parent_mailmerge(
            self, file_name: str = "parent mailmerge.csv") -> None:
        '''Exports each parent contact for use in mail merges.

        The basic export includes student address, parent names and parent contact details.

        Args:
            file_name: The file path to save the csv export, including filename.
        '''
        url = f"https://{self.school_code}.compass.education/Services/FileDownload/CsvRequestHandler?type=24"
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

    def export_addresses( self, file_name: str = "address export.csv") -> None:
        '''Exports contact information for all Compass users.
        
        Includes address, phone number and email address.
        
        Args:
            file_name: The file path to save teh csv export, including filename.
        '''
        payload = f'{{"action":"read","filters":[],"sorters":[],"page":1,"start":0,"limit":{limit},"addRecords":false}}'

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

    def get_classes_for_subject(self, subject_id: int) -> list[dict]:
        """Downloads a CSV with subject metadata.
        
        Args:
            subject_id: The Compass subject id number for the subject.

        Returns:
            A list of dictionaries containing metadata for each class in the
            subject.
        """
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.headers.update(headers)
        url = f"https://{self.school_code}.compass.education/Services/Subjects.svc/GetStandardClassesOfSubject?sessionstate=readonly&_dc={current_ms_time()}"
        payload = f'{{"subjectId":{subject_id},"page":1,"start":0,"limit":50,"sort":"[{{\\"property\\":\\"name\\",\\"direction\\":\\"ASC\\"}}]"}}'
        r = self.post(url, data=payload)
        decoded_response = r.json()['d']['data']
        del self.headers['Content-Type']
        return decoded_response

    def get_subjects(self, academic_group: int = -1) -> list[dict]:
        """Gets a list of all subjects in an academic group.
        
        Args:
            academic_group: The academic group to export. Defaults to the
                currently active group.
                
        Returns:
            A list of dictionaries containing subject metadata.
        """
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.headers.update(headers)
        subjects_url = f"https://{self.school_code}.compass.education/Services/Subjects.svc/GetSubjectsInAcademicGroup?sessionstate=readonly&_dc={current_ms_time()}"

        subjects = []
        page = 1
        payload = f'{{"academicGroupId":{academic_group},"includeDataSyncSubjects":true,"page":{page},"start":{50*page-50},"limit":50,"sort":"[{{\\"property\\":\\"importIdentifier\\",\\"direction\\":\\"ASC\\"}}]"}}'
        r = self.post(subjects_url, data=payload)
        new_subjects = r.json()['d']['data']
        subjects += new_subjects
        while len(new_subjects) == 50:
            page += 1
            payload = f'{{"academicGroupId":{academic_group},"includeDataSyncSubjects":true,"page":{page},"start":{50*page-50},"limit":50,"sort":"[{{\\"property\\":\\"importIdentifier\\",\\"direction\\":\\"ASC\\"}}]"}}'
            r = self.post(subjects_url, data=payload)
            new_subjects = r.json()['d']['data']
            subjects += new_subjects

        del self.headers['Content-Type']
        return subjects

    def get_classes(self, academic_group: int = -1) -> list[dict]:
        """Gets a list of all classes in an academic group.
        
        Args:
            academic_group: The academic group to export. Defaults to the
                currently active group.
                
        Returns:
            A list of dictionaries containing class metadata.
        """
        subjects = self.get_subjects(academic_group)
        classes = []
        for subject in subjects:
            new_classes = self.get_classes_for_subject(subject['id'])
            classes += new_classes
        return classes

    def get_class_enrolments(self,
                             activity_id: int,
                             add_activity_id: bool = False) -> list[dict]:
        """Gets a list of all enrolments in a class.
        
        Args:
            activity_id: An activity id for one lesson for the class.
        
        Returns:
            A list of dictionaries containing student metadata.
        """
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        self.headers.update(headers)

        payload = f'{{"activityId":{activity_id},"page":1,"start":0,"limit":25}}'
        url = f"https://{self.school_code}.compass.education/Services/Activity.svc/GetEnrolmentsByActivityId?sessionstate=readonly&_dc={current_ms_time()}"
        r = self.post(url, data=payload)
        new_enrolments = r.json()['d']
        if add_activity_id:
            for enrolment in new_enrolments:
                enrolment.update({"activity_id": activity_id})

        del self.headers['Content-Type']

        return new_enrolments

    def export_attendance_cases_halfday(self,
                                        start_date: str,
                                        finish_date: str,
                                        save_dir: str,
                                        included_exited: bool = True):
        """Exports attendance data in the CASES half-day csv format.
        
        Args:
            start_date: The start date for the export as yyyy-mm-dd
            finish_date: The finish date for the export as yyyy-mm-dd
            save_dir: The folder to save the export into.
        """
        payload = f'{{"type":"5","parameters":"{{\\"reportName\\":\\"cases21HalfDayCsv\\",\\"filename\\":\\"CASES21_HalfDay.csv\\",\\"startDateIn\\":\\"{start_date}T13:00:00.000Z\\",\\"finishDateIn\\":\\"{finish_date}T13:00:00.000Z\\",\\"includeExitedStudents\\":{str(included_exited).lower()},\\"minimumAbsentDays\\":\\"\\",\\"includeOverSixteens\\":true,\\"includePLCStudents\\":true,\\"yearLevelId\\":\\"\\",\\"campuses\\":\\"\\",\\"semester\\":\\"1\\",\\"collection\\":\\"Semester 1\\",\\"modifiedSinceDateIn\\":null,\\"userIds\\":\\"19311\\",\\"yearLevels\\":\\"7|8|9|10\\",\\"startDatePickerAttendanceByDayReport\\":\\"2023-05-19T14:00:00.000Z\\",\\"exportDatePickerFullSchoolAuditRollReport\\":\\"2023-05-19T14:00:00.000Z\\",\\"teachingDaysNumber\\":\\"8\\",\\"includeComments\\":true,\\"yearLevelsPreSchool\\":\\"\\",\\"yearLevelsPrimary\\":\\"\\",\\"yearLevelsMiddle\\":\\"\\",\\"yearLevelsSenior\\":\\"\\",\\"groupBy\\":null,\\"ethnicities\\":\\"\\",\\"yearLevelIds\\":\\"\\",\"formGroups\\":\\"\\"}}"}}'
        self.long_running_file_request(payload, save_dir)


def get_report_cycle_id(cycles, year, name):
    for c in cycles:
        if c['year'] == year and c['name'] == name:
            return c['id']
    return None
