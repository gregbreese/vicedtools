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
"""Functions for automating the export of data from VASS.

Deprecated: The VASSWebDriver class is being replaced by VASSSession, a 
requests.Sessions based class."""

from __future__ import annotations

from io import StringIO
import math
import re
import requests
import time
import xml.etree.ElementTree as ET
from warnings import warn

import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.ie.service import Service
from selenium.webdriver.ie.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from webdriver_manager.microsoft import IEDriverManager


def click_with_retry(element: WebElement, test: callable[[], bool]) -> bool:
    """Tries fives times to click a webdriver element, stopping if test passes.
    
    Used to deal with IE driver unreliability.
    
    Args:
        element: A webdriver element.
        test: A function that returns True if click was successful.
    
    Returns:
        Whether click was successful.
    """
    tries = 0
    while tries < 5:
        element.click()
        if test():
            return True
        time.sleep(0.2)
        tries += 1
    return False


def find_window(driver: WebDriver, window_title: str) -> str:
    """Find the window handle with a particular title.
    
    Args:
        driver: A webdriver instance.
        window_title: The window title to locate.
        
    Returns:
        The window handle of the window, if found. Otherwise, None.
    """
    current = driver.current_window_handle
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if driver.title == window_title:
            driver.switch_to.window(current)
            return handle
    driver.switch_to.window(current)
    return None


def is_menu_item_displayed(driver: WebDriver, xpath_expr: str) -> bool:
    """Tests to see if a given menu item is displayed in VASS.
    
    Used to deal with unreliable clicks in IE.
    
    Args:
        driver: An instance of VASSWebDriver.
        xpath_expr: An xpath expression that matches the menu item.
    """
    cf = current_frame(driver)
    driver.switch_to.default_content()
    driver.switch_to.frame('main')
    menu_item = driver.find_element(By.XPATH, xpath_expr)
    is_displayed = menu_item.is_displayed()
    driver.switch_to.default_content()
    driver.switch_to.frame(cf)
    return is_displayed


def current_frame(driver: WebDriver) -> str:
    """Returns the name of the webdriver's current frame."""
    return driver.execute_script("""
            var frame = window.frameElement;
            if (!frame) {
                return 'root of window named ' + document.title;
            }
            return frame.name;
            """)


class VASSWebDriver(webdriver.Ie):

    def __init__(self,
                 iedriver_path: str,
                 username="",
                 password="",
                 grid_password="",
                 os_type='win32'):
        """Creates a webdriver with VASS authentication completed.

        Deprecated: Use the VASSSession class to reduce the reliance on
        Internet Explorer.
    
        Creates an instance of selenium.webdriver.Ie and authenticates to VASS.
        
        Args:
            iedriver_path: The path to geckodriver.exe
            username: The username to login with
            password: The password to login with
            grid_password: The grid password to login with. A sequence of
                tuples, each tuple being the grid coordinate of the next
                password character. Must be given in top-> bottom, left->
                right order.
            os_type: The os type, defaults to win32 as win64 is slow

        Returns:
            An instance of selenium.webdriver.ie with authentication to
            VASS completed.
        """

        warn(f'{self.__class__.__name__} will be deprecated. Use VASSSession', DeprecationWarning, stacklevel=2)

        options = webdriver.IeOptions()
        options.native_events = False
        #options.ignore_protected_mode_settings = True
        options.ignore_zoom_level = True
        options.persistent_hover = True
        options.add_additional_option("unexpectedAlertBehaviour", "accept")
        options.add_additional_option("disable-popup-blocking", True)

        super().__init__(executable_path=iedriver_path, options=options)

        self.launch_window = self.current_window_handle
        # login to VASS
        self.get("https://www.vass.vic.edu.au/login/")

        current_handles = self.window_handles
        login_link = WebDriverWait(self, 20).until(
            EC.element_to_be_clickable((By.NAME, "boslogin")))
        self.execute_click(login_link)
        time.sleep(0.5)
        WebDriverWait(self, 20).until(EC.new_window_is_opened(current_handles))
        handle = find_window(self, "Login To VASS")
        self.switch_to.window(handle)
        self.main_window = self.current_window_handle

        # username/password auth
        self.find_element(By.NAME, "username").send_keys(username)
        self.find_element(By.NAME, "password").send_keys(password)
        self.execute_click(
            self.find_element(By.XPATH, "//input[contains(@name, 'Login')]"))

        # password grid auth
        WebDriverWait(self, 10).until(
            EC.presence_of_element_located((By.NAME, 'PASSCODEGRID')))
        pattern = r'type=input value=(?P<value>[A-Za-z0-9!@#\$%\^&\*~\+=]) name=PASSCODEGRID MaxCol="8" MaxList="64" PassListLength="6" QuadrantNum="[0-9]" ColumnNum="(?P<col>[0-9])" RowNum="(?P<row>[0-9])"'
        ms = re.findall(pattern, self.page_source)
        grid_values = {}
        for m in ms:
            grid_values[(m[1], m[2])] = m[0]
        grid_password_characters = "".join(
            [grid_values[i] for i in grid_password])
        self.find_element(By.XPATH,
                          "//input[contains(@name, 'PassCode')]").send_keys(
                              grid_password_characters)
        self.execute_click(
            self.find_element(By.XPATH,
                              "//input[contains(@name, 'AcceptButton')]"))
        WebDriverWait(self, 20).until(EC.title_contains("VASS - "))
        pattern = "VASS - (?P<school>[A-Za-z ]+) - Year (?P<year>[0-9]{4})"
        m = re.match(pattern, self.title)
        if m:
            self.school = m.group('school')
            self.year = m.group('year')
        time.sleep(1)

    def execute_click(self, element):
        self.set_script_timeout(1)
        try:
            self.execute_script("arguments[0].click()", element)
        except TimeoutException:
            pass
        self.set_script_timeout(30)  #default

    def change_year(self, year: str) -> None:
        """Changes the year in VASS.
        
        Args:
            year: The year to change to.
        """
        self.switch_to.default_content()
        # ignore tempramental menu and just inject the menu click
        WebDriverWait(self, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
        current_handles = self.window_handles
        menu_item = self.find_element(By.XPATH,
                                      "//*[contains(text(),'Change Year')]")
        self.execute_click(menu_item)
        time.sleep(0.5)
        WebDriverWait(self, 20).until(EC.new_window_is_opened(current_handles))
        for handle in self.window_handles:
            self.switch_to.window(handle)
            if self.title == "Change Code/Year":
                break
        WebDriverWait(self, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "VASSFrame")))
        #self.switch_to.frame('VASSFrame')
        year_field = self.find_element(By.NAME, "Year")
        year_field.send_keys(year)
        continue_button = self.find_element(By.XPATH, "//input[@type='submit']")
        self.execute_click(continue_button)
        time.sleep(1)
        self.switch_to.window(self.main_window)
        self.year = year

    def external_results(self, file_name):
        """Saves the student external results (study scores) to a csv.
        
        Args:
            file_name: The file name to save the data as.    
        """
        external_results_url = "https://www.vass.vic.edu.au/results/reports/GradedAssessmentResultsByClass/GAResultsReport.vass?StudySequenceCode=ALL&ClassCode=&Semester=ALL&ReportOrder=Unit&exportReport=Y"
        s = requests.session()
        # copy cookies from selenium session
        for cookie in self.get_cookies():
            c = {cookie['name']: cookie['value']}
            s.cookies.update(c)
        # request student details file
        r = s.get(external_results_url)

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
        s = requests.session()
        # copy cookies from selenium session
        for cookie in self.get_cookies():
            c = {cookie['name']: cookie['value']}
            s.cookies.update(c)
        # request student details file
        r = s.get(url)
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
        user_agent = self.execute_script("return navigator.userAgent;")

        s = requests.session()
        headers = {"User-Agent": user_agent}
        s.headers.update(headers)
        # copy cookies from selenium session
        for cookie in self.get_cookies():
            c = {cookie['name']: cookie['value']}
            s.cookies.update(c)
        # request student details file
        r = s.get(personal_details_url)
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

    # TODO: See if data can be downloaded directly from https://www.vass.vic.edu.au/results/reports/GATResultsSummary/GATResultsSummary_Display.cfm?&yr=" + year_level + "&form=" + form_group + "&myIndex=1&myTotal=1"
    def gat_summary(self, file_name: str) -> None:
        """Extracts student GAT results and saves them to a csv.
        
        Args:
            file_name: The file name for the csv to save the data to.
        """
        self.switch_to.default_content()
        WebDriverWait(self, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
        menu_item = WebDriverWait(self, 10).until(
            EC.presence_of_element_located((By.ID, "item7_3_1")))  # GAT Summary
        self.execute_click(menu_item)
        current_handles = self.window_handles
        # run report
        try:
            button = WebDriverWait(self, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//input[(@name='btnRunReport') and (@type='submit')]")))
        except TimeoutException:
            self.switch_to.default_content()
            WebDriverWait(self, 10).until(
                EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
            menu_item = self.find_element(By.ID, "item7_3_1")
            self.execute_click(menu_item)
            button = WebDriverWait(self, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//input[(@name='btnRunReport') and (@type='submit')]")))
        self.execute_click(button)
        time.sleep(0.5)
        WebDriverWait(self, 20).until(EC.new_window_is_opened(current_handles))
        gat_window = find_window(
            self, f"GAT Results Summary for {self.school} - {self.year}")
        self.switch_to.window(gat_window)
        students = []
        time.sleep(0.5)
        while (True):
            self.switch_to.frame('VASSFrame')

            report_data = self.find_element(By.ID, "reportData")
            data = report_data.get_attribute('innerHTML')
            try:
                root = ET.fromstring(data.strip())
            except ET.ParseError:
                time.sleep(2)  # try giving page more time to load
                report_data = self.find_element(By.ID, "reportData")
                data = report_data.get_attribute('innerHTML')
                root = ET.fromstring(data.strip())
            for child in root.iter('student'):
                students.append(child.attrib)
            self.switch_to.parent_frame()
            self.switch_to.frame('VASSTop')
            e = self.find_element(By.ID, "idNext")  # next subject
            if e.get_attribute('style') == "DISPLAY: none":
                break  # no more classes
            self.switch_to.parent_frame()
            time.sleep(0.1)
        self.switch_to.parent_frame()
        self.switch_to.frame('VASSTop')
        self.execute_click(self.find_element(By.ID, "idClose"))
        self.switch_to.window(self.main_window)
        df = pd.DataFrame(students)
        df.rename(columns={
            "CandNum": "Student Number",
            "name": "Student Name"
        },
                  inplace=True)
        df.to_csv(file_name, index=False)

    def school_scores(self, file_name: str) -> None:
        """Extracts school score data for all GAs and saves to a csv.
        
        Args:
            file_name: The filename to save the data to.
        """
        # create a requests session to avoid working with IE
        s = requests.session()
        user_agent = self.execute_script("return navigator.userAgent;")
        headers = {"User-Agent": user_agent}
        s.headers.update(headers)
        # copy cookies from selenium session
        for cookie in self.get_cookies():
            c = {cookie['name']: cookie['value']}
            s.cookies.update(c)

        school_scores = []

        # get data about what subjects and GAs have students
        for cycle in ['5', '6', '8']:
            school_results_metadata_url = f"https://www.vass.vic.edu.au/results/reports/SchoolAssessedResultsBySchool/SchoolAssessedResultsBySchool_Frameset.cfm?Cycle={cycle}&UnitCode=ALL&GA=0&AssessedElsewhere=false&AdjustPaper=true"
            r = s.get(school_results_metadata_url)
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
                r = s.get(results_url)

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
        s.close()
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

    def predicted_scores(self, file_name: str):
        """Exports student achieved and predicted scores from Report 17.
        
        Uses the currently selected year in VASS even though the Report 17 UI
        allows for year selection.

        Args:
            file_name: The csv to save to.
        """
        self.switch_to.default_content()
        WebDriverWait(self, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
        menu_item = WebDriverWait(self, 10).until(
            EC.presence_of_element_located((By.ID, "item2_6_1")))
        self.execute_click(menu_item)
        time.sleep(0.5)
        button = WebDriverWait(self, 10).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 "//input[@value='Run VCE Data Service Reporting System']")))
        current_handles = self.window_handles
        self.execute_click(button)
        WebDriverWait(self, 20).until(EC.new_window_is_opened(current_handles))
        handle = find_window(
            self, f"VCE Data System Reporting for {self.school} - {self.year}")
        self.switch_to.window(handle)
        # open report 17
        self.switch_to.frame('VASSTop')
        report17 = self.find_element(By.ID, 'btnReport17')
        self.execute_click(report17)
        # select year
        year_select_element = WebDriverWait(self, 5).until(
            EC.presence_of_element_located(
                (By.ID, 'mainHolder_Report17_ddlYear')))
        select = Select(year_select_element)
        select.select_by_visible_text(self.year)
        # select all subjects, trying doing this with action chains later, might be faster
        time.sleep(0.5)
        subject_select_element = WebDriverWait(self, 5).until(
            EC.presence_of_element_located(
                (By.ID, 'mainHolder_Report17_lstSubjects')))
        select = Select(subject_select_element)
        n_subjects = len(select.options)
        for i in range(n_subjects):
            select_element = WebDriverWait(self, 5).until(
                EC.presence_of_element_located(
                    (By.ID, 'mainHolder_Report17_lstSubjects')))
            select = Select(select_element)
            select.select_by_index(i)
            time.sleep(0.5)
        button = self.find_element(By.ID, 'mainHolder_btnReport')
        self.execute_click(button)
        time.sleep(1)
        results = []
        while True:
            WebDriverWait(self, 10).until(
                EC.presence_of_element_located((By.ID, 'mainHolder_pnlReport')))
            page_source = self.page_source
            # get subject
            pattern = r'>(?P<subject>[A-Za-z :\(\)]+):&nbsp;&nbsp;Student Results by Study'
            m = re.search(pattern, page_source)
            subject = m.group('subject')
            # get student results
            pattern = '''<TR>\\r\\n<TD align=left style="BORDER-TOP: black 1px solid; BORDER-RIGHT: black 1px solid; WIDTH: 150px; BORDER-BOTTOM: black 1px solid; FONT-WEIGHT: normal; BORDER-LEFT: black 1px solid">&nbsp;(?P<surname>[A-Za-z-']+)<\/TD>\\r\\n<TD align=left style="BORDER-TOP: black 1px solid; BORDER-RIGHT: black 1px solid; WIDTH: 150px; BORDER-BOTTOM: black 1px solid; FONT-WEIGHT: normal; BORDER-LEFT: black 1px solid">&nbsp;(?P<firstname>[A-Za-z- ]+)<\/TD>\\r\\n<TD align=center style="BORDER-TOP: black 1px solid; BORDER-RIGHT: black 1px solid; WIDTH: 100px; BORDER-BOTTOM: black 1px solid; FONT-WEIGHT: normal; BORDER-LEFT: black 1px solid">(?P<yearlevel>[0-9]+)<\/TD>\\r\\n<TD align=center style="BORDER-TOP: black 1px solid; BORDER-RIGHT: black 1px solid; WIDTH: 100px; BORDER-BOTTOM: black 1px solid; FONT-WEIGHT: normal; BORDER-LEFT: black 1px solid">(?P<classgroup>[A-Za-z0-9 ]+)<\/TD>\\r\\n<TD align=center style="FONT-SIZE: 8pt; BORDER-TOP: black 1px solid; BORDER-RIGHT: black 1px solid; WIDTH: 100px; BORDER-BOTTOM: black 1px solid; FONT-WEIGHT: normal; BORDER-LEFT: black 1px solid">(?P<achieved>[0-9\.]+)<\/TD>\\r\\n<TD align=center style="FONT-SIZE: 8pt; BORDER-TOP: black 1px solid; BORDER-RIGHT: black 1px solid; WIDTH: 100px; BORDER-BOTTOM: black 1px solid; FONT-WEIGHT: normal; BORDER-LEFT: black 1px solid">(?P<predicted>[0-9\.]+|N\/A)<\/TD><\/TR>'''
            ms = re.findall(pattern, page_source)
            new_results = [{
                'Year': self.year,
                'Subject': subject,
                'Surname': m[0],
                'FirstName': m[1],
                'YearLevel': m[2],
                'ClassGroup': m[3],
                'Achieved': m[4],
                'Predicted': m[5]
            } for m in ms]
            results += new_results
            # go to next subject
            next_button = self.find_element(
                By.NAME, 'ctl00$mainHolder$ReportHeader1$btnNext')
            if next_button.get_attribute('disabled') == 'true':
                break
            self.execute_click(next_button)
            time.sleep(1)
        close_button = self.find_element(By.ID,
                                         'mainHolder_ReportHeader1_btnClose')
        self.execute_click(close_button)
        self.close()
        self.switch_to.window(self.main_window)
        df = pd.DataFrame.from_records(results)
        df.to_csv(file_name, index=False)

    def moderated_coursework_scores(self, file_name: str) -> None:
        """Extracts moderated scores for school scores for all GAs and saves to a csv.
        
        Args:
            file_name: The filename to save the data to.
        """
        # create a requests session to avoid working with IE
        s = requests.session()
        user_agent = self.execute_script("return navigator.userAgent;")
        headers = {"User-Agent": user_agent}
        s.headers.update(headers)
        # copy cookies from selenium session
        for cookie in self.get_cookies():
            c = {cookie['name']: cookie['value']}
            s.cookies.update(c)

        # get data about what studies/ga's there is data for
        url = "https://www.vass.vic.edu.au/school/reports/StatmodStatistics/StatmodStatistics_Frameset.cfm?StudySequenceCode=All&GANum=All&CycleNum=All"
        r = s.get(url)
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
            r = s.get(url)

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
        s.close()
        if moderated_scores:
            df = pd.DataFrame.from_records(moderated_scores,
                                           columns=[
                                               "Subject", "GA Number",
                                               "GA Name", "Max score",
                                               "School score", "Moderated score"
                                           ])
            df.to_csv(file_name, index=False)
