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
        self.year = "2022"

    def change_year(self, year: str) -> None:
        """Changes the year in VASS.
        
        Args:
            year: The year to change to.
        """
        change_year_url = "https://www.vass.vic.edu.au/sysad/ChangeCode/ChangeCode_Action.cfm"
        payload = [("Year", year)]
        r = self.post(change_year_url, data=payload)

        confirm_url = f"https://www.vass.vic.edu.au/sysad/ChangeCode/ChangeCode_ConfirmChange.cfm?Year={year}"
        r = self.get(confirm_url)
        self.year = year

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


    def gat_summary(self, file_name: str) -> None:
        """Extracts student GAT results and saves them to a csv.
        
        Args:
            file_name: The file name for the csv to save the data to.
        """
        groups_url = 'https://www.vass.vic.edu.au/results/reports/GATResultsSummary/GATResultsSummary_Frameset.cfm?YearLevel=ALL&FormGroup='
        r = self.get(groups_url)

        form_groups_list_pattern = "saYearLevels = \[(.*?)]"
        form_groups_list_match = re.search(form_groups_list_pattern, r.text)
        form_groups_pattern = "'(.*?)'"
        form_groups = re.findall(form_groups_pattern, form_groups_list_match.group(0))
        year_lvl_list_pattern = "saFormGroups = \[(.*?)]"
        year_lvl_list_match = re.search(year_lvl_list_pattern, r.text)
        year_level_pattern = "'(.*?)'"
        year_levels = re.findall(year_level_pattern, year_lvl_list_match.group(0))

        students = []

        total = len(year_levels)
        for index, form_group, year_level in zip(range(1,total+1),year_levels,form_groups):
            gat_results_url = f'https://www.vass.vic.edu.au/results/reports/GATResultsSummary/GATResultsSummary_Display.cfm?&yr={year_level}&form={form_group}&myIndex={index}&myTotal={total}'
            r = self.get(gat_results_url)
            
            xml_start_pattern = r'<xml id="reportData">'
            xml_start_match = re.search(xml_start_pattern, r.text)
            xml_end_pattern = r'</xml>'
            xml_end_match = re.search(xml_end_pattern, r.text)
            start = xml_start_match.span(0)[1]
            end = xml_end_match.span(0)[0]

            root = ET.fromstring(r.text[start:end].strip())
            for child in root.iter('student'):
                students.append(child.attrib)

        df = pd.DataFrame(students)
        df.rename(columns={
            "CandNum": "Student Number",
            "name": "Student Name"
        },
                  inplace=True)
        df.to_csv(file_name, index=False)

    def predicted_scores(self, file_name: str, **kwargs):
        """Exports student achieved and predicted scores from Report 17.

        Defaults to downloading data for the currently selected year in VASS.

        Args:
            file_name: The csv to save to.
            year: Optional, download data for the given year.
            years: Optional, download data for the given list of years. Will be
                ignored if the parameter year is given. 
        """
        if 'year' in kwargs:
            years = [kwargs['year']]
        elif 'years' in kwargs:
            years = kwargs['years']
        else:
            years = [self.year]

        # login to vce data system
        url = "https://www.vass.vic.edu.au/school/VCEDataSystem/Reporting/VCEDSReporting_Frameset.cfm?TestOnly=false"
        r = self.get(url)
        pattern = r"https://vceds.vass.vic.edu.au/accessdispatcher.aspx\?message=[0-9]*"
        m = re.search(pattern, r.text)
        url = m.group()
        r = self.get(url)
        # open report17 and get hidden form fields
        url = "https://vceds.vass.vic.edu.au/Reports/Display/Report17_StudentResultsByStudy.aspx"
        r = self.get(url)

        # get results for each year in turn
        headers = {"Referer": "https://vceds.vass.vic.edu.au/Reports/Display/Report17_StudentResultsByStudy.aspx"}
        self.headers.update(headers)
        results = []
        for year in years:
            # select year and refresh subject list
            viewstate, viewstategenerator, eventvalidation = get_vceds_hidden_params(r.text)
            payload = report17_select_year_payload(viewstate, viewstategenerator, eventvalidation, year)
            url = "https://vceds.vass.vic.edu.au/Reports/Display/Report17_StudentResultsByStudy.aspx"
            r = self.post(url, data=payload)
            subjects = report17_subjects(r.text)

            # select all subjects
            viewstate, viewstategenerator, eventvalidation = get_vceds_hidden_params(r.text)
            payload = report17_select_subject_payload(viewstate, viewstategenerator, eventvalidation, year, subjects)
            url = "https://vceds.vass.vic.edu.au/Reports/Display/Report17_StudentResultsByStudy.aspx"
            r = self.post(url, data=payload)
            
            # open first results page
            viewstate, viewstategenerator, eventvalidation = get_vceds_hidden_params(r.text)
            payload = report17_results_button_payload(viewstate, viewstategenerator, eventvalidation, year, subjects)
            headers = {"X-MicrosoftAjax": "Delta=true", 
                    "X-Requested-With": "XMLHttpRequest"
                    }
            self.headers.update(headers)
            url = "https://vceds.vass.vic.edu.au/Reports/Display/Report17_StudentResultsByStudy.aspx"
            r = self.post(url, data=payload)
            for key in headers:
                del self.headers[key]
            results += report17_extract_results(r.text, year)

            for _ in subjects[1:]:
                # get next subject
                viewstate, viewstategenerator, eventvalidation = get_vceds_hidden_params(r.text)
                payload = report17_next_results_payload(viewstate, viewstategenerator, eventvalidation)
                url = "https://vceds.vass.vic.edu.au/Reports/Display/Report17_StudentResultsByStudy.aspx"
                r = self.post(url, data=payload)
                results += report17_extract_results(r.text, year)

            # close results page
            viewstate, viewstategenerator, eventvalidation = get_vceds_hidden_params(r.text)
            payload = report17_close_results_payload(viewstate, viewstategenerator, eventvalidation)
            url = "https://vceds.vass.vic.edu.au/Reports/Display/Report17_StudentResultsByStudy.aspx"
            r = self.post(url, data=payload)
            
        del self.headers["Referer"]

        df = pd.DataFrame.from_records(results)
        df.to_csv(file_name, index=False)




def get_vceds_hidden_params(response: str) -> tuple[str, str, str]:
    """Returns the hidden form fields for VCE data service pages."""
    viewstategenerator_pattern = '((__VIEWSTATEGENERATOR" value=")|(__VIEWSTATEGENERATOR\|))(?P<value>[A-Z0-9]*)["|]'
    m = re.search(viewstategenerator_pattern, response)
    if m:
        viewstategenerator = m.group('value')
    else:
        viewstategenerator = ""
    eventvalidation_pattern = '((__EVENTVALIDATION" value=")|(__EVENTVALIDATION\|))(?P<value>.*?)["|]'
    m = re.search(eventvalidation_pattern, response)
    if m:
        eventvalidation = m.group('value')
    else:
        eventvalidation = ""
    viewstate_pattern = '((__VIEWSTATE" value=")|(__VIEWSTATE\|))(?P<value>.*?)["|]'
    m = re.search(viewstate_pattern, response)
    if m:
        viewstate = m.group('value')
    else:
        viewstate = ""
    return viewstate, viewstategenerator, eventvalidation

def report17_subjects(response: str) -> list[tuple[str,str]]:
    """Returns the subjects that can be selected for Report 17."""
    subject_pattern = '<option (?:selected="selected" )?value="([0-9]{1,3})">(.*?)</option>'
    subjects = re.findall(subject_pattern, response)
    return subjects

def report17_select_year_payload(viewstate: str, viewstategenerator: str, eventvalidation: str, year: str) -> list[tuple[str,str]]:
    """Returns the form data for selecting a new year in the VCE DS Report 17."""
    payload = [("__EVENTTARGET","ctl00$mainHolder$Report17$ddlYear"),
               ("__EVENTARGUMENT",""),
               ("__LASTFOCUS",""),
               ("__VIEWSTATE",viewstate),
               ("__VIEWSTATEGENERATOR",viewstategenerator),
               ("__EVENTVALIDATION", eventvalidation),
               ("ctl00$pnlReports1to6_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports7to9_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports10to14_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports15to16_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports17to18_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports19to20_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$mainHolder$Report17$ddlYear", year),
               ("ctl00$mainHolder$Report17$hfList", ""),
              ]
    return payload

def report17_select_subject_payload(viewstate: str, viewstategenerator: str, eventvalidation: str, year: str, subjects: list[str]) -> list[tuple[str,str]]:
    """Returns the form data for selecting subjects in the VCE DS Report 17."""
    part1 = [("__EVENTTARGET","ctl00$mainHolder$Report17$lstSubjects"),
               ("__EVENTARGUMENT",""),
               ("__LASTFOCUS",""),
               ("__VIEWSTATE",viewstate),
               ("__VIEWSTATEGENERATOR",viewstategenerator),
               ("__EVENTVALIDATION", eventvalidation),
               ("ctl00$pnlReports1to6_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports7to9_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports10to14_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports15to16_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports17to18_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports19to20_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$mainHolder%24Report17$ddlYear", year)
              ]
    part2 = [("ctl00$mainHolder$Report17$lstSubjects", idx) for idx, name in subjects]
    part3 = [("ctl00$mainHolder$Report17$hfList", "")]
    return part1 + part2 + part3

def report17_results_button_payload(viewstate: str, viewstategenerator: str, eventvalidation: str, year: str, subjects: list[str]) -> list[tuple[str,str]]:
    """Returns the form data for getting the first page of results for Report 17."""
    part1 = [("ctl00$ScriptManager1", "ctl00$mainHolder$UpdatePanel1|ctl00$mainHolder$btnReport"),
               ("__EVENTTARGET",""),
               ("__EVENTARGUMENT",""),
               ("__LASTFOCUS",""),
               ("__VIEWSTATE",viewstate),
               ("__VIEWSTATEGENERATOR",viewstategenerator),
               ("__EVENTVALIDATION", eventvalidation),
               ("ctl00$pnlReports1to6_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports7to9_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports10to14_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports15to16_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports17to18_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports19to20_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$mainHolder$Report17$ddlYear", year),
              ]
    part2 = [("ctl00$mainHolder$Report17$lstSubjects", idx) for idx, name in subjects]
    part3 = [("ctl00$mainHolder$Report17$rblSchoolType","0"),
             ("ctl00$mainHolder$Report17$hfList", ""),
             ("__ASYNCPOST","true"),
             ("ctl00$mainHolder$btnReport","Report"),
            ]
    return part1 + part2 + part3

def report17_next_results_payload(viewstate: str, viewstategenerator: str, eventvalidation: str) -> list[tuple[str,str]]:
    """Returns the form data for getting the next page of results for Report 17."""
    payload = [("__EVENTTARGET",""),
               ("__EVENTARGUMENT",""),
               ("__VIEWSTATE",viewstate),
               ("__VIEWSTATEGENERATOR",viewstategenerator),
               ("__EVENTVALIDATION", eventvalidation),
               ("ctl00$pnlReports1to6_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports7to9_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports10to14_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports15to16_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports17to18_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports19to20_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$mainHolder$ReportHeader1$btnNext",">>"),
               ("mainHolder_WebChartViewer1_JsChartViewerState","3*320\x1e2*490\x1e1*20\x1e0*50"),
               ("mainHolder_WebChartViewer1_callBackURL", "/Reports/Display/Report17_StudentResultsByStudy.aspx?cdLoopBack=1"),
              ]
    return payload

def report17_close_results_payload(viewstate: str, viewstategenerator: str, eventvalidation: str) -> list[tuple[str,str]]:
    """Returns the form data for closing the results page for Report 17."""
    payload = [("__EVENTTARGET",""),
               ("__EVENTARGUMENT",""),
               ("__VIEWSTATE",viewstate),
               ("__VIEWSTATEGENERATOR",viewstategenerator),
               ("__EVENTVALIDATION", eventvalidation),
               ("ctl00$pnlReports1to6_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports7to9_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports10to14_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports15to16_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports17to18_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$pnlReports19to20_CollapsiblePanelExtender_ClientState","false"),
               ("ctl00$mainHolder$ReportHeader1$btnClose","Close"),
               ("mainHolder_WebChartViewer1_JsChartViewerState","3*320\x1e2*490\x1e1*20\x1e0*50"),
               ("mainHolder_WebChartViewer1_callBackURL", "/Reports/Display/Report17_StudentResultsByStudy.aspx?cdLoopBack=1"),
              ]
    return payload

def report17_extract_results(response: str, year: str) -> list[dict]:
    """Returns the results from a results page of the VCE DS Report 17."""
    subject_name_pattern = r'>(?P<subject>[A-Za-z :\(\)]+):&nbsp;&nbsp;Student Results by Study'
    m = re.search(subject_name_pattern, response)
    subject = m.group('subject')
    # get student results
    pattern = '''<tr>\\r\\n(?:\\t)*<td align="left" style="font-weight:normal;width:150px;BORDER-LEFT: black 1px solid; BORDER-Bottom: black 1px solid; BORDER-Top: black 1px solid; BORDER-RIGHT: black 1px solid;">&nbsp;(?P<surname>[A-Za-z-']+)<\/td><td align="left" style="font-weight:normal;width:150px;BORDER-LEFT: black 1px solid; BORDER-Bottom: black 1px solid; BORDER-Top: black 1px solid; BORDER-RIGHT: black 1px solid;">&nbsp;(?P<firstname>[A-Za-z- ]+)<\/td><td align="center" style="font-weight:normal;width:100px;BORDER-LEFT: black 1px solid; BORDER-Bottom: black 1px solid; BORDER-Top: black 1px solid; BORDER-RIGHT: black 1px solid;">(?P<yearlevel>[0-9]+)<\/td><td align="center" style="font-weight:normal;width:100px;BORDER-LEFT: black 1px solid; BORDER-Bottom: black 1px solid; BORDER-Top: black 1px solid; BORDER-RIGHT: black 1px solid;">(?P<classgroup>[A-Za-z0-9 ]+)<\/td><td align="center" style="font-size:8pt;font-weight:normal;width:100px;BORDER-LEFT: black 1px solid; BORDER-Bottom: black 1px solid; BORDER-Top: black 1px solid; BORDER-RIGHT: black 1px solid;">(?P<achieved>[0-9\.]+)<\/td><td align="center" style="font-size:8pt;font-weight:normal;width:100px;BORDER-LEFT: black 1px solid; BORDER-Bottom: black 1px solid; BORDER-Top: black 1px solid; BORDER-RIGHT: black 1px solid;">(?P<predicted>[0-9\.]+|N\/A)<\/td>\\r\\n(?:\\t)*<\/tr>'''
    ms = re.findall(pattern, response)
    new_results = [{
        'Year': year,
        'Subject': subject,
        'Surname': m[0],
        'FirstName': m[1],
        'YearLevel': m[2],
        'ClassGroup': m[3],
        'Achieved': m[4],
        'Predicted': m[5]
    } for m in ms]
    return new_results
