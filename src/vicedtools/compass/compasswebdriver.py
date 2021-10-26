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
"""A class derived from webdriver.Firefox that includes Compass authentication."""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
import glob
import os
import requests
import time
from typing import Protocol
import zipfile


import browser_cookie3
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# TODO: implement auth from local environment variables/config file
# TODO: implement Chrome support
class CompassWebDriver(webdriver.Firefox):
    """WebDriver extension that stores the Compass school code."""

    def __init__(self,
                 school_code: str,
                 geckodriver_path: str,
                 authenticator: CompassAuthenticator,
                 download_path: str = "./"):
        """Creates a webdriver with Compass authentication completed.
    
        Creates an instance of selenium.webdriver.Firefox and authenticates either
        through a manually entered username/password or through cookies stored in
        the locally installed Firefox installation.
        
        Args:
            school_code: Your school's compass school code.
            geckodriver_path: The path to geckodriver.exe
            authenticator: An instance of CompassAuthenticator to perform the
                required authentication with Compass.
            download_path: The path to download any files to.


        Returns:
            An instance of selenium.webdriver.Firefox with authentication to
            Compass completed.
        """
        self.school_code = school_code

        profile = webdriver.FirefoxProfile()
        profile.set_preference("browser.download.folderList", 2)
        profile.set_preference("browser.download.manager.showWhenStarting",
                               False)
        profile.set_preference("browser.download.dir", download_path)
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk",
                               "text/csv, application/zip")

        webdriver.firefox.webdriver.WebDriver.__init__(
            self, executable_path=geckodriver_path, firefox_profile=profile)

        authenticator.authenticate(self)

    def set_download_dir(self, directory: str) -> None:
        """Sets the download directory.
        
        Args:
            directory: The new download path.
        """
        self.command_executor._commands["SET_CONTEXT"] = (
            "POST", "/session/$sessionId/moz/context")
        self.execute("SET_CONTEXT", {"context": "chrome"})
        self.execute_script(
            """
            Services.prefs.setStringPref('browser.download.dir', arguments[0]);
            """, directory)
        self.execute("SET_CONTEXT", {"context": "content"})

    def export_sds(self,
               download_path: str = ".\\",
               download_wait: int = 10 * 60,
               append_date: bool = False) -> None:
        '''Exports class enrolment and teacher information from Compass.

        Downloads the Microsoft SDS export from Compass using Selenium and the
        Firefox webdriver.

        Requires access to SDS Export rights in the Subjects and Classes page.

        Will save four files in the provided path:
            StudentEnrollment.csv: contains student->class mappings
            Teacher.csv: contains teacher id information
            TeacherRoster.csv: contains teacher->class mappings
            Section.csv: contains class id information

        Args:
            download_path: The directory to save the export. Must use \\ slashes in 
                            windows.
            download_wait: Optional; the amount of time to wait for Compass to 
                generate the export, default 10 mins.
            append_date: If True, append today's date to the filenames in
                yyyy-mm-dd format.
        '''
        self.set_download_dir(download_path)

        # download Microsoft SDS export
        self.get("https://" + self.school_code +
                ".compass.education/Learn/Subjects.aspx")
        # Export menu
        WebDriverWait(self,
                    20).until(EC.element_to_be_clickable(
                        (By.ID, "button-1020"))).click()
        # Export menu item
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable((By.ID, "menuitem-1025-itemEl"))).click()
        # Submit button
        WebDriverWait(self,
                    20).until(EC.element_to_be_clickable(
                        (By.ID, "button-1103"))).click()
        # Yes button
        WebDriverWait(self,
                    20).until(EC.element_to_be_clickable(
                        (By.ID, "button-1120"))).click()

        # TODO: Poll to see when download is done
        time.sleep(download_wait)

        files = glob.glob(download_path +
                        "\\Bulk SDS SCV Download - Generated - *.zip")
        # newest_time = datetime.min
        # file_to_extract = ""
        # for file in files:
        #     pattern = r'Bulk SDS SCV Download - Generated - (?P<date>[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{4}[APM]{2}).zip'
        #     m = re.search(pattern, file)
        #     date = m.group('date')
        #     dt = datetime.strptime(date,"%Y-%m-%d_%I%M%p")
        #     if dt > newest_time:
        #         file_to_extract = file
        file_to_extract = files[0]
        contents = [
            "StudentEnrollment.csv", "Teacher.csv", "TeacherRoster.csv",
            "Section.csv"
        ]
        with zipfile.ZipFile(file_to_extract, 'r') as zip_ref:
            for content in contents:
                if append_date:
                    today = datetime.today().strftime('%Y-%m-%d')
                    parts = content.split('.')
                    new_filename = parts[0] + " " + today + "." + parts[1]
                    info = zip_ref.get_info(content)
                    info.filename = new_filename
                    zip_ref.extract(new_filename, path=download_path)
                else:
                    zip_ref.extract(file_to_extract, path=download_path)
        os.remove(file_to_extract)

    def export_student_details(self,
                           download_path: str = "student details.csv") -> None:
        '''Exports student details from Compass.

        Args:
            download_path: The file path to save the csv export, including filename.
        '''
        headers = {
            "User-Agent":
                "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
        }
        s = requests.session()
        s.headers.update(headers)
        # copy cookies from selenium session
        for cookie in self.get_cookies():
            c = {cookie['name']: cookie['value']}
            s.cookies.update(c)
        # request student details file
        r = s.get(
            "https://" + self.school_code +
            ".compass.education/Services/FileDownload/CsvRequestHandler?type=38")
        with open(download_path, "xb") as f:
            f.write(r.content)

    def discover_academic_years(self) -> list(str):
        """Discovers the academic years that exist in Compass.
        
        Useful for downloading learning tasks.

        Returns:
            A list of the names of each academic year.
        """
        self.get(
            "https://" + self.school_code +
            ".compass.education/Communicate/LearningTasksAdministration.aspx")
        # Open Reports tab
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable((By.ID, "tab-1101-btnIconEl"))).click()
        # Open dropdown menu
        WebDriverWait(self,
                    20).until(EC.element_to_be_clickable(
                        (By.ID, "ext-gen1188"))).click()
        # Get dropdown menu items
        items = self.find_elements_by_class_name("x-boundlist-item")
        academic_years = [item.text for item in items]
        return academic_years

    def export_learning_tasks(self,
                          academic_year: str,
                          download_path: str = ".\\") -> None:
        """Exports all learning tasks data from Compass.
        
        Downloads the Learning Tasks exports from Compass using Selenium and the
        Firefox webdriver.

        Will prompt for Compass login details.
        Requires access to Learning Tasks Administration.

        Data is saved as "[download_path]/LearningTasks-[academic_year].csv".

        Args:
            download_path: The directory to save the export. Must use \\ slashes in 
                            windows.
            academic_year: Which Compass academic year to download the export for.
        """
        self.set_download_dir(download_path)
        self.get(
            "https://" + self.school_code +
            ".compass.education/Communicate/LearningTasksAdministration.aspx")
        # Open Reports tab
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable((By.ID, "tab-1101-btnIconEl"))).click()
        # Open dropdown menu
        WebDriverWait(self,
                    20).until(EC.element_to_be_clickable(
                        (By.ID, "ext-gen1188"))).click()
        # select the academic year
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                "//*[contains(text(),'" + academic_year + "')]"))).click()
        # Press export button
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable((By.ID, "button-1061-btnInnerEl"))).click()
        for _i in range(600):  # 10 minutes
            time.sleep(1)
            try:
                # Get cancel button
                button = self.find_element_by_xpath(
                    "//*[contains(text(),'Cancel')]")
            except NoSuchElementException:
                button = self.find_element_by_xpath(
                    "//*[contains(text(),'Close')]")
                button.click()
                break

    # TODO: Get cycles not on first page
    def discover_progress_report_cycles(self,
                                        published_only: bool = True) -> list(str):
        """Discovers the available progress report cycles.

        Currently only discovers cycles on first page.

        Args:
            published_only: if true, only return those cycles set as "Published to 
                All".

        Returns:
            A list of the names of each progress report cyle.
        """
        # open progress reports page
        self.get("https://" + self.school_code +
                ".compass.education/Organise/Reporting/GPA/Default.aspx")
        # open cycles tab
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(),'Cycles')]"))).click()
        # all published progress reports
        if published_only:
            elements = self.find_elements_by_xpath(
                "//table/tbody/tr/td/div[contains(text(),'Published To All')]/parent::*/parent::*/child::td[1]/div/a"
            )
        else:
            elements = self.find_elements_by_xpath(
                "//table/tbody/tr/td/div/parent::*/parent::*/child::td[1]/div/a")
        progress_report_cycles = [e.text for e in elements]

        return progress_report_cycles

    def export_progress_report(self,
                           cycle: str,
                           download_path: str = ".\\") -> None:
        """Export progress report data.
        
        Data is saved as "[download_path]/[cycle].csv"

        Args:
            cycle: The name of the progress report cycle to export.
            download_path: The directory to save the export. Must use \\ slashes in 
                            windows.
        """
        self.set_download_dir(download_path)
        # open progress reports page
        self.get("https://" + self.school_code +
                ".compass.education/Organise/Reporting/GPA/Default.aspx")
        # open cycles tab
        #button = driver.find_element_by_xpath("//*[contains(text(),'Cycles')]")
        #button.click()
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[contains(text(),'Cycles')]"))).click()
        # open selected cycle
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                "//td/div/a[contains(text(), '" + cycle + "')]"))).click()
        # export link
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable(
                (By.LINK_TEXT, "Export results to CSV"))).click()

        # Export button
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH,
                "//a/span/span/span[contains(text(),'Export')]"))).click()
        # Confirmation OK button
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a/span/span/span[contains(text(),'OK')]"))).click()
        for _i in range(600):  # 10 minutes
            time.sleep(1)
            try:
                # Get cancel button
                button = self.find_element_by_xpath(
                    "//*[contains(text(),'Cancel')]")
            except NoSuchElementException:
                button = self.find_element_by_xpath(
                    "//*[contains(text(),'Close')]")
                button.click()
                break

    def discover_report_cycles(self,
                           published_only: bool = True) -> list(tuple(str)):
        """Discovers the available report cycles.

        Args:
            published_only: if true, only return those cycles set to allow student 
                access.

        Returns:
            A list of the names of each report cyle.
        """
        # open reports page
        self.get("https://" + self.school_code +
                ".compass.education/Organise/Reporting/Cycles.aspx")

        rows = self.find_elements_by_xpath("//div/div[3]/div/table/tbody/tr")
        cycles = []
        for row in rows:
            published_to_students = row.find_element_by_xpath("./td[5]").text
            if not published_only or published_to_students == "Yes":
                year = row.find_element_by_xpath("./td[1]").text
                name = row.find_element_by_xpath("./td[2]").text
                cycles.append((year, name))

        return cycles


    def export_report_cycle(self,
                            year: str,
                            title: str,
                            download_path: str = ".\\") -> None:
        """Export progress report data.
        
        Data is saved as "[download_path]/SemesterReportAllResultsCsvExport Generated - [%Y-%m-%d_%I%M%p].csv"

        Args:
            year: The year of the report cycle to export.
            title: The title of the report cycle to export.
            download_path: The directory to save the export. Must use \\ slashes in 
                            windows.
        """
        self.set_download_dir(download_path)

        self.get("https://" + self.school_code +
                ".compass.education/Organise/Reporting/Cycles.aspx")
        # open cycle config page
        rows = self.find_elements_by_xpath("//div/div[3]/div/table/tbody/tr")
        for row in rows:
            row_year = row.find_element_by_xpath("./td[1]").text
            row_title = row.find_element_by_xpath("./td[2]").text
            if (row_year == year) and (row_title == title):
                row.find_element_by_xpath("./td[2]/div/a").click()
                break
        # export all results
        # menu
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[@id='button-1076-btnWrap']"))).click()
        # all results item
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//*[@id='menuitem-1084-textEl']"))).click()
        # ok button
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a/span/span/span[contains(text(),'OK')]"))).click()
        # wait for download
        for _i in range(600):  # 10 minutes
            time.sleep(1)
            try:
                # Get cancel button
                button = self.find_element_by_xpath(
                    "//*[contains(text(),'Cancel')]")
            except NoSuchElementException:
                button = self.find_element_by_xpath(
                    "//*[contains(text(),'Close')]")
                button.click()
                break


class CompassAuthenticator(Protocol):
    """An abstract class for generic Compass Authenticator objects."""

    @abstractmethod
    def authenticate(self, driver: CompassWebDriver) -> None:
        """Authenticates the given webdriver with Compass."""
        raise NotImplementedError


class CompassCLIAuthenticator(CompassAuthenticator):
    """A Compass Authenticator that gets login details from CLI prompt."""

    def authenticate(self, driver: CompassWebDriver):
        driver.get("https://" + driver.school_code + ".compass.education/")
        username_field = self.find_element_by_name("username")
        username = input("Compass username: ")
        username_field.send_keys(username)
        password_field = self.find_element_by_name("password")
        password = input("Compass password: ")
        password_field.send_keys(password)
        submit_button = self.find_element_by_name("button1")
        submit_button.click()


class CompassBrowserCookieAuthenticator(CompassAuthenticator):
    """A Compass Authenticator that gets login details from local Firefox cookies."""

    def authenticate(self, driver: CompassWebDriver):
        cj = browser_cookie3.firefox(domain_name=driver.school_code +
                                     '.compass.education')
        driver.get("https://" + driver.school_code + '.compass.education/')
        for c in cj:
            cookie_dict = {
                'name': c.name,
                'value': c.value,
                'domain': c.domain,
                'expires': c.expires,
                'path': c.path
            }
            driver.add_cookie(cookie_dict)
