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
"""Functions for automating the export of data from Compass."""

from __future__ import annotations

from io import StringIO
import requests
import time
import xml.etree.ElementTree as ET

from lxml import etree
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def click_with_retry(element, test):
    tries = 0
    while tries < 5:
        element.click()
        if test():
            return True
        time.sleep(0.2)
        tries += 1
    return False

def find_window(driver, window_title):
    current = driver.current_window_handle
    for handle in driver.window_handles:
        driver.switch_to.window(handle)
        if driver.title == window_title:
            driver.switch_to.window(current)
            return handle
    driver.switch_to.window(current)
    return None

def is_menu_item_displayed(driver, xpath_expr):
    cf = current_frame(driver)
    driver.switch_to.default_content()
    driver.switch_to.frame('main')
    menu_item = driver.find_element_by_xpath(xpath_expr)
    is_displayed = menu_item.is_displayed()
    driver.switch_to.default_content()
    driver.switch_to.frame(cf)
    return is_displayed

def current_frame(driver):
    return driver.execute_script("""
            var frame = window.frameElement;
            if (!frame) {
                return 'root of window named ' + document.title;
            }
            return frame.name;
            """)

# TODO: Implement username/password/grid passsword input from config file.
class VASSWebDriver(webdriver.Ie):
    def __init__(self,
                 iedriver_path: str,
                 auth: str = 'kwargs', username="", password="", grid_password=""):
        """Creates a webdriver with VASS authentication completed.
    
        Creates an instance of selenium.webdriver.Ie and authenticates to VASS.
        
        Args:
            iedriver_path: The path to geckodriver.exe
            auth: If 'kwargs' will use the username, password and grid layout
                provided as keyword arguments.

        Returns:
            An instance of selenium.webdriver.ie with authentication to
            VASS completed.
        """
        ieCapabilities = DesiredCapabilities.INTERNETEXPLORER.copy()
        ieCapabilities["nativeEvents"] = False
        ieCapabilities["unexpectedAlertBehaviour"] = "accept"
        ieCapabilities["ignoreProtectedModeSettings"] = True
        ieCapabilities["disable-popup-blocking"] = True
        ieCapabilities["enablePersistentHover"] = True
        ieCapabilities["ignoreZoomSetting"] = True
        
        self.driver = webdriver.Ie(executable_path=iedriver_path, desired_capabilities=ieCapabilities)

        self.launch_window = self.driver.current_window_handle
        # login to VASS
        self.driver.get("https://www.vass.vic.edu.au/login/")
        time.sleep(2)
        login_link = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.NAME, "boslogin")))
        click_with_retry(login_link, lambda: find_window(self.driver, "Login To VASS"))
        #login_link = self.driver.find_element_by_name("boslogin")
        #login_link.click()
        time.sleep(1)
        handle = find_window(self.driver, "Login To VASS")
        self.driver.switch_to.window(handle)
        self.main_window = self.driver.current_window_handle
        if auth == 'kwargs':
            # username/password
            username_field = self.driver.find_element_by_name("username")
            username_field.send_keys(username)
            password_field = self.driver.find_element_by_name("password")
            password_field.send_keys(password)
            login_button = self.driver.find_element_by_xpath("//input[contains(@name, 'Login')]")
            login_button.click()
            time.sleep(3)
            # password grid
            elements = self.driver.find_elements_by_xpath("//table/tbody/tr/td/form/table/tbody/tr[1]/td/input")
            grid_values = {}
            for e in elements:
                grid_values[(e.get_attribute("ColumnNum"),e.get_attribute("RowNum"))] = e.get_attribute("value")
            grid_password_characters = "".join([grid_values[i] for i in grid_password])
            password_field = self.driver.find_element_by_xpath("//input[contains(@name, 'PassCode')]")
            password_field.send_keys(grid_password_characters)
            accept_button = self.driver.find_element_by_xpath("//input[contains(@name, 'AcceptButton')]")
            accept_button.click()
            time.sleep(2)
        # TODO: correct this!
        self.year = "2021"

    def change_year(self, year):
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame('nav')
        system_admin_menu = self.driver.find_element_by_xpath("//*[contains(text(),'SYSTEM ADMIN')]")
        click_with_retry(system_admin_menu, lambda: is_menu_item_displayed(self.driver, "//*[contains(text(),'Change Year')]" ))
        self.driver.switch_to.parent_frame()
        self.driver.switch_to.frame('main')
        menu_item = self.driver.find_element_by_xpath("//*[contains(text(),'Change Year')]")
        menu_item.click()
        time.sleep(3)
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if self.driver.title == "Change Code/Year":
                break
        self.driver.switch_to.frame('VASSFrame')
        year_field = self.driver.find_element_by_name("Year")
        year_field.send_keys(year)
        continue_button = self.driver.find_element_by_xpath("//input[@type='submit']")
        continue_button.click()
        self.driver.switch_to.window(self.main_window)
        self.year = year

    def external_results(self, file_name):
        external_results_url = "https://www.vass.vic.edu.au/results/reports/GradedAssessmentResultsByClass/GAResultsReport.vass?StudySequenceCode=ALL&ClassCode=&Semester=ALL&ReportOrder=Unit&exportReport=Y"
        s = requests.session()
        # copy cookies from selenium session
        for cookie in driver.driver.get_cookies():
            c = {cookie['name']: cookie['value']}
            s.cookies.update(c)
        # request student details file
        r = s.get(
            external_results_url)

        names = ["Unit Code", "Unit Name", "Class Code", "Semester", "Teacher Code",
                 "Teacher Name", "Year Level", "Form Group", "Student Number", 
                 "Student Name", "Gender", "Unit 3 Result", "Unit 4 Result", 
                 "GA 1 Result", "GA 2 Result", "GA 3 Result", "Study Score", "Blank"]
        df = pd.read_csv(StringIO(r.content.decode('utf-8')), sep="|", names=names, skiprows=1)
        df.to_csv(file_name, index=False)
        
    def personal_details_summary(self,file_name):
        personal_details_url = "https://www.vass.vic.edu.au/student/reports/StudentPersonalDetailsSummary/PersonalDetailsSummary.vass?yearLevel=ALL&formGroup=&course=ALL&reportType=1&includeAddress=N&reportOrder=yrLevel"
        s = requests.session()
        # copy cookies from selenium session
        for cookie in driver.driver.get_cookies():
            c = {cookie['name']: cookie['value']}
            s.cookies.update(c)
        # request student details file
        r = s.get(
            personal_details_url)
        names = ["Year Level","Form Group","Student Number","Family Name","First Name",
                 "Second Name","External ID","Gender","Phone Number","Date of Birth", 
                 "Course"]
        df = pd.read_csv(StringIO(r.content.decode('utf-8')), sep="|", names=names, 
                         skiprows=1, skipfooter=1,engine='python')
        df.fillna("", inplace=True)
        df.to_csv(file_name, index=False)

    # TODO: Work in progress
    def school_scores(self, file_name):
        # open ranked school scores report page
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame('nav')
        results_admin_menu = self.driver.find_element_by_xpath("//*[contains(text(),'RESULTS ADMIN')]")
        click_with_retry(results_admin_menu, lambda: is_menu_item_displayed(self.driver, "//*[@id='item7_3']" ))
        results_admin_menu.click()
        time.sleep(1)
        self.driver.switch_to.parent_frame()
        self.driver.switch_to.frame('main')
        menu_item = self.driver.find_element_by_id("item7_3") # VCE Reports
        hover = ActionChains(self.driver).move_to_element(menu_item)
        hover.perform()
        time.sleep(0.2)
        menu_item = self.driver.find_element_by_id("item7_3_1")
        hover = ActionChains(self.driver).move_to_element(menu_item)
        hover.perform()
        menu_item = self.driver.find_element_by_id("item7_3_3") # School Scores
        hover = ActionChains(self.driver).move_to_element(menu_item)
        hover.perform()
        time.sleep(0.2)
        menu_item = self.driver.find_element_by_id("item7_3_3_1") 
        hover = ActionChains(self.driver).move_to_element(menu_item)
        hover.perform()
        menu_item = self.driver.find_element_by_id("item7_3_3_2") # Subject ranked summaries
        hover = ActionChains(self.driver).move_to_element(menu_item)
        hover.perform()
        menu_item.click()

    def gat_summary(self, file_name):
        # export GAT summary
        self.driver.switch_to.frame('nav')
        results_admin_menu = self.driver.find_element_by_xpath("//*[contains(text(),'RESULTS ADMIN')]")
        results_admin_menu.click()
        time.sleep(1)
        self.driver.switch_to.parent_frame()
        self.driver.switch_to.frame('main')
        menu_item = self.driver.find_element_by_id("item7_3") # VCE Reports
        hover = ActionChains(self.driver).move_to_element(menu_item)
        hover.perform()
        time.sleep(1)
        menu_item = self.driver.find_element_by_id("item7_3_1") # GAT Summary
        menu_item.click()
        time.sleep(3)
        button = self.driver.find_element_by_xpath("//input[(@name='btnRunReport') and (@type='submit')]") # Run report
        button.click()
        time.sleep(3)
        main_window = self.driver.window_handles[1] # fix
        gat_window = self.driver.window_handles[2] # fix
        self.driver.switch_to.window(gat_window)
        students = []
        while(True):
            self.driver.switch_to.frame('VASSFrame')
            data = self.driver.find_element_by_id("reportData").get_attribute('innerHTML')
            root = ET.fromstring(data.strip())
            for child in root.iter('student'):
                students.append(child.attrib)
            self.driver.switch_to.parent_frame()
            self.driver.switch_to.frame('VASSTop')
            try:
                self.driver.find_element_by_id("idNext").click() # next subject
            except ElementNotInteractableException:
                break
            self.driver.switch_to.parent_frame()
        self.driver.switch_to.parent_frame()
        self.driver.switch_to.frame('VASSTop')
        self.driver.find_element_by_id("idClose").click()
        self.driver.switch_to.window(self.main_window)
        df = pd.DataFrame(students)
        df.to_csv(file_name, index=False)

    def school_scores(self, file_name):
        # open ranked school scores report page
        # TODO: possibly can open this directly with a javascript click instead of driver click
        self.driver.switch_to.default_content()
        self.driver.switch_to.frame('nav')
        results_admin_menu = self.driver.find_element_by_xpath("//*[contains(text(),'RESULTS ADMIN')]")
        click_with_retry(results_admin_menu, lambda: is_menu_item_displayed(self.driver, "//*[@id='item7_3']" ))
        results_admin_menu.click()
        time.sleep(1)
        self.driver.switch_to.parent_frame()
        self.driver.switch_to.frame('main')
        menu_item = self.driver.find_element_by_id("item7_3") # VCE Reports
        hover = ActionChains(self.driver).move_to_element(menu_item)
        hover.perform()
        time.sleep(0.2)
        menu_item = self.driver.find_element_by_id("item7_3_1")
        hover = ActionChains(self.driver).move_to_element(menu_item)
        hover.perform()
        menu_item = self.driver.find_element_by_id("item7_3_3") # School Scores
        hover = ActionChains(self.driver).move_to_element(menu_item)
        hover.perform()
        time.sleep(0.2)
        menu_item = self.driver.find_element_by_id("item7_3_3_1") 
        hover = ActionChains(self.driver).move_to_element(menu_item)
        hover.perform()
        menu_item = self.driver.find_element_by_id("item7_3_3_2") # Subject ranked summaries
        hover = ActionChains(self.driver).move_to_element(menu_item)
        hover.perform()
        menu_item.click()
        # scrape all of the school scores
        school_scores = []
        cycle_names = ["5 - U3 SAT Results", "6 - Unit 3 School-assessed Coursework", "8 - Unit 4 SAT and SAC"]
        for cycle in cycle_names:
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame('main')
            self.driver.find_element_by_xpath(f"//select[@name='CycleNum']/option[text()='{cycle}']").click()
            button = self.driver.find_element_by_xpath("//input[@value='Run Ranked School Scores Report']")
            try:
                self.driver.execute_script("arguments[0].click();", button)
            except TimeoutException:
                pass
            handle = find_window(self.driver, f"Ranked School Scores Report for Glen Waverley Secondary College - {year}")
            self.driver.switch_to.window(handle)
            while(True):
                self.driver.switch_to.frame("VASSFrame")
                data = self.driver.find_element_by_id("reportData").get_attribute('innerHTML')
                root = ET.fromstring(data.strip())
                max_score = root.get("MaxScore")
                params = {'Max Score': max_score}
                for child in root.iter('param'):
                        params[child.attrib['name']] = child.attrib['value']
                del params['Students Assessed Elsewhere']
                for child in root.iter('student'):
                    school_scores.append( { **child.attrib, **params})
                self.driver.switch_to.parent_frame()
                self.driver.switch_to.frame('VASSTop')
                try:
                    self.driver.find_element_by_id("idNext").click() # next subject
                except ElementNotInteractableException:
                    break
                self.driver.switch_to.parent_frame()
            self.driver.switch_to.parent_frame()
            self.driver.switch_to.frame('VASSTop')
            self.driver.find_element_by_id("idClose").click()
            self.driver.switch_to.window(self.main_window)
        results_df =  pd.DataFrame(school_scores)
        results_df.to_csv(file_name)