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
"""A requests Session class for exporting data from VASS."""

from __future__ import annotations

from io import StringIO
import math
import re
import requests
import time
import xml.etree.ElementTree as ET

import pandas as pd

class VassLoginError(Exception):
    """Error with vass login."""
    pass

class VASSSession(requests.Session):

    def __init__(self,
                 username="",
                 password="",
                 grid_password="",
                 ):
        """Creates a requests Session with VASS authentication completed.
    
        Args:
            username: The username to login with
            password: The password to login with
            grid_password: The grid password to login with. A sequence of
                tuples, each tuple being the grid coordinate of the next
                password character. Must be given in top-> bottom, left->
                right order.
        
        Returns:
            An instance of requests.Session with authentication to
            VASS completed.
        """
        requests.sessions.Session.__init__(self)

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
                "Accept":"text/html, application/xhtml+xml, image/jxr, */*"}
        self.headers.update(headers)

        # username and password login
        payload = {"Login":"Login", "password":password, "username":username}
        submit_login_url = "https://www.vass.vic.edu.au/login/VerifyAuthLogin.cfm"
        r = self.post(submit_login_url, data=payload)

        if "https://www.vass.vic.edu.au/login/schoolcode.cfm" not in r.text:
            # login unsuccessful
            raise VassLoginError()

        # get passcode grid and login with grid code
        school_code_url = "https://www.vass.vic.edu.au/login/schoolcode.cfm"
        r = self.get(school_code_url)
            
        pattern = r'passlist="(?P<s>.*?)"'
        m = re.search(pattern, r.text)
        grid_values = m.group('s').split(',')
        grid_password = [(int(a), int(b)) for (a,b) in grid_password]
        grid_response = "".join([grid_values[(b-1)*8 + (a-1)] for (a,b) in grid_password])
        payload = []
        for value in grid_values:
            payload.append(("PASSCODEGRID", value))
        payload.append(("PassCode", grid_response))
        payload.append(("Year", "2022"))
        payload.append(("AcceptButton", "Accept"))
        school_code_submit_url = "https://www.vass.vic.edu.au/login/SchoolCodeAction.cfm"
        r = self.post(school_code_submit_url, data=payload)
        if "https://www.vass.vic.edu.au/menu/Home.cfm" not in r.text:
            raise  VassLoginError()

    def change_year(self, year: str) -> None:
        """Changes the year in VASS.
        
        Args:
            year: The year to change to.
        """
        change_year_url = "https://www.vass.vic.edu.au/sysad/ChangeCode/ChangeCode_Action.cfm"
        payload = [("Year", year)]
        r = self.post(change_year_url, data=payload)

        confirm_url = f"https://www.vass.vic.edu.au/sysad/ChangeCode/ChangeCode_ConfirmChange.cfm?Year={year}"
        r = s.get(confirm_url)

    def external_results(self, file_name):
        """Saves the student external results (study scores) to a csv.
        
        Args:
            file_name: The file name to save the data as.    
        """
        external_results_url = "https://www.vass.vic.edu.au/results/reports/GradedAssessmentResultsByClass/GAResultsReport.vass?StudySequenceCode=ALL&ClassCode=&Semester=ALL&ReportOrder=Unit&exportReport=Y"
        r = self.get(external_results_url)

        names = [
            "Unit Code", "Unit Name", "Class Code", "Semester", "Teacher Code",
            "Teacher Name", "Year Level", "Form Group", "Student Number",
            "Student Name", "Gender", "Unit 3 Result", "Unit 4 Result",
            "GA 1 Result", "GA 2 Result", "GA 3 Result", "Study Score", "Blank"
        ]
        df = pd.read_csv(StringIO(r.content.decode('utf-8')),
                         sep="|",
                         names=names,
                         skiprows=1)
        df.to_csv(file_name, index=False)

    def school_program_summary(self, file_name: str, report: str = "vce"):
        """Saves the school program summary to a csv file.
        
        Args:
            file_name: The file name to save the data to.
            report: "vce", "vet" or "vcal"
        """
        base_url = "https://www.vass.vic.edu.au/schoolprog/reports/SchoolProgramSummary/SchoolProgramSummary.vass?TeacherNum=&UnitLevel=0&Semester=0&ReportSelection="
        url = base_url + report

        # request student details file
        r = self.get(url)
        names = [
            "Unit Code", "Unit Name", "Teacher Code", "Teacher Name",
            "Semester", "Class Code", "Class Size", "Time Block"
        ]
        df = pd.read_csv(StringIO(r.content.decode('utf-8')),
                         sep="|",
                         names=names,
                         skiprows=1,
                         skipfooter=1,
                         engine='python')
        df.fillna("", inplace=True)
        df.to_csv(file_name, index=False)

    def personal_details_summary(self, file_name: str):
        """Saves the student personal details summary to a csv file.
        
        Args:
            file_name: The file name to save the data to.
        """
        personal_details_url = "https://www.vass.vic.edu.au/student/reports/StudentPersonalDetailsSummary/PersonalDetailsSummary.vass?yearLevel=ALL&formGroup=&course=ALL&reportType=1&includeAddress=N&reportOrder=yrLevel"

        # request student details file
        r = self.get(personal_details_url)
        names = [
            "Year Level", "Form Group", "Student Number", "Family Name",
            "First Name", "Second Name", "External ID", "Gender",
            "Phone Number", "Date of Birth", "Course"
        ]
        df = pd.read_csv(StringIO(r.content.decode('utf-8')),
                         sep="|",
                         names=names,
                         skiprows=1,
                         skipfooter=1,
                         engine='python')
        df.fillna("", inplace=True)
        df.to_csv(file_name, index=False)


    def school_scores(self, file_name: str) -> None:
        """Extracts school score data for all GAs and saves to a csv.
        
        Args:
            file_name: The filename to save the data to.
        """
        school_scores = []

        # get data about what subjects and GAs have students
        for cycle in ['5', '6', '8']:
            school_results_metadata_url = f"https://www.vass.vic.edu.au/results/reports/SchoolAssessedResultsBySchool/SchoolAssessedResultsBySchool_Frameset.cfm?Cycle={cycle}&UnitCode=ALL&GA=0&AssessedElsewhere=false&AdjustPaper=true"
            r = self.get(school_results_metadata_url)
            try:
                # get list of unit names
                unit_name_list_pattern = r"""UnitNames\t= \[(.*?)];"""
                unit_name_list_match = re.search(unit_name_list_pattern, r.text)
                unit_name_pattern = r'"(.*?)"'
                unit_name_matches = re.findall(unit_name_pattern,
                                            unit_name_list_match.group(0))
                # get list of unit codes
                unit_code_list_pattern = r"""naUnits \t= \[(.*?)];"""
                unit_code_list_match = re.search(unit_code_list_pattern, r.text)
                unit_code_pattern = r"'(.*?)'"
                unit_code_matches = re.findall(unit_code_pattern,
                                            unit_code_list_match.group(0))
                # get list of ga numbers
                ga_number_list_pattern = r"""naGAs \t= \[.*?];"""
                ga_number_list_match = re.search(ga_number_list_pattern, r.text)
                ga_number_pattern = r"'(.*?)'"
                ga_number_matches = re.findall(ga_number_pattern,
                                            ga_number_list_match.group(0))
                # get list of ga names
                ga_name_list_pattern = r"""GANames \t= \[.*?];"""
                ga_name_list_match = re.search(ga_name_list_pattern, r.text)
                ga_name_pattern = r'"(.*?)"'
                ga_name_matches = re.findall(ga_name_pattern,
                                            ga_name_list_match.group(0))
                # get list of max scores
                max_scores_list_pattern = r"""naGAMaxScores\t= \[.*?];"""
                max_scores_list_match = re.search(max_scores_list_pattern, r.text)
                max_scores_number_pattern = r"'(.*?)'"
                max_scores_matches = re.findall(max_scores_number_pattern,
                                                max_scores_list_match.group(0))
            except AttributeError:
                print(f"Error downloading school scores for year {self.year}.")
                return

            # get all the results
            
            metadata = zip(unit_code_matches, unit_name_matches, ga_number_matches,
                        ga_name_matches, max_scores_matches)
            for unit_code, unit_name, ga_number, ga_name, max_score in metadata:
                results_url = f"https://www.vass.vic.edu.au/results/reports/SchoolAssessedResultsBySchool/SchoolAssessedResultsBySchoolCRS_Display.cfm?UnitCode={unit_code}&UnitName={unit_name}&GA={ga_number}&GAName={ga_name}&GAMaxScore={max_score}&AssessedElsewhere=false&AdjustPaper=true&myIndex=1&myTotal=1&ReportName=Ranked School Scores Report"
                r = self.get(results_url)

                xml_start_pattern = r'<xml id="reportData">'
                xml_start_match = re.search(xml_start_pattern, r.text)
                xml_end_pattern = r'</xml>'
                xml_end_match = re.search(xml_end_pattern, r.text)
                start = xml_start_match.span(0)[1]
                end = xml_end_match.span(0)[0]

                root = ET.fromstring(r.text[start:end].strip())
                max_score = root.get("MaxScore")
                siar = root.get("SIAR")
                siar_max_score = root.get("SIARMaxScore")
                params = {
                    'Max Score': max_score,
                    "SIAR": siar,
                    "SIAR Max Score": siar_max_score
                }
                for child in root.iter('param'):
                    params[child.attrib['name']] = child.attrib['value']
                del params['Students Assessed Elsewhere']
                for child in root.iter('student'):
                    school_scores.append({**child.attrib, **params})
        if school_scores:
            # convert to a DataFrame and save scores
            df = pd.DataFrame(school_scores)
            subject_names = {}
            unit_names = df["Unit"]
            pattern = "(?P<code>[A-Z]{2}[0-9]{2})[34] - (?P<name>[A-Z :\(\)]+) [34]"
            for unit in unit_names:
                m = re.match(pattern, unit)
                if m:
                    subject_names[unit] = m.group('name')
            df["Unit Code"] = df["Unit"].str[:4]
            df["Unit Name"] = df["Unit"].map(subject_names)
            #df.drop(["Unit"], inplace=True)
            df.drop_duplicates(inplace=True)
            df.rename(columns={
                "CandNum": "Student Number",
                "name": "Student Name",
                "focus_area": "Focus Area",
                "class_cd": "Class",
                "result": "Result"
            },
                      inplace=True)
            df.to_csv(file_name, index=False)

    def moderated_coursework_scores(self, file_name: str) -> None:
        """Extracts moderated scores for school scores for all GAs and saves to a csv.
        
        Args:
            file_name: The filename to save the data to.
        """
        # get data about what studies/ga's there is data for
        url = "https://www.vass.vic.edu.au/school/reports/StatmodStatistics/StatmodStatistics_Frameset.cfm?StudySequenceCode=All&GANum=All&CycleNum=All"
        r = self.get(url)
        var_names = [
            'saCycle', 'saStudyCode', 'saSequenceCode',
            ' saCombinedSequenceCode', 'saGANum', 'saCycleDescription',
            'saSequenceDescription', 'saGAName', 'saMaxScore',
            'saModerationGroup', 'saVCEorVET'
        ]
        var_quotes = [
            "'", "'", "'", "'", "'", '"', '"', '"', "'", "'", "'", "'"
        ]
        metadata = []
        for idx, var_name in enumerate(var_names):
            list_pattern = var_name + r"""[ \t]+= \[(.*?)];"""
            list_match = re.search(list_pattern, r.text)
            if var_quotes[idx] == "'":
                items_pattern = r"'(.*?)'"
            else:
                items_pattern = r'"(.*?)"'
            item_matches = re.findall(items_pattern, list_match.group(0))
            metadata.append(item_matches)

        # get moderated score data for each study and ga

        # values are given in reference to x,y in the graph
        left = 45
        right = 666
        top = 30
        bottom = 364

        moderated_scores = []
        # get moderation statistics
        for cycle, study_code, sequence_code, combined_sequence_code, ga_num, cycle_desc, sequence_desc, ga_name, max_score, moderation_group, vce_or_vet in zip(
                *metadata):
            url = f"https://www.vass.vic.edu.au/school/reports/StatmodStatistics/StatmodStatistics_Display.cfm?&Cycle={cycle}&CycleDesc={cycle_desc}&StudyCode={study_code}&SequenceCode={sequence_code}&CombinedSequenceCode={combined_sequence_code}&GANum={ga_num}&SequenceDescription={sequence_desc}&GAName={ga_name}&MaxScore={max_score}&ModerationGroup={moderation_group}&VCEorVET={vce_or_vet}&myIndex=1&myTotal=34"
            r = self.get(url)

            map_pattern = r"""<map id="[0-9]*-map" name="[0-9]*-map">(.*?)</map>"""
            m = re.search(map_pattern, r.text, flags=re.DOTALL)
            map_items = m.group(1)
            graph_element_pattern = r"""<area.*?shape="(.*?)".*?plot-([0-9]).*? coords="(.*?)" />"""
            graph_elements = re.findall(graph_element_pattern,
                                        map_items,
                                        flags=re.DOTALL)

            for e in graph_elements:
                if e[0] == 'circle':
                    if e[1] == '1':
                        x, y, r = [int(a) for a in e[2].split(',')]
                        moderated_scores.append(
                            (sequence_desc, ga_num, ga_name, max_score,
                             math.ceil(
                                 (x - left) / (right - left) * int(max_score)),
                             round(
                                 (bottom - y) / (bottom - top) * int(max_score),
                                 1)))
        if moderated_scores:
            df = pd.DataFrame.from_records(moderated_scores,
                                           columns=[
                                               "Subject", "GA Number",
                                               "GA Name", "Max score",
                                               "School score", "Moderated score"
                                           ])
            df.to_csv(file_name, index=False)
