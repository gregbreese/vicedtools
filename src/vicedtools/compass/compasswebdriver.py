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
import os
import requests
import time
from typing import Protocol
import zipfile

import browser_cookie3
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, JavascriptException, TimeoutException
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
        self.download_path = download_path

    def set_download_dir(self, path: str) -> None:
        """Sets the download directory.
        
        Args:
            path: The new download path.
        """
        self.command_executor._commands["SET_CONTEXT"] = (
            "POST", "/session/$sessionId/moz/context")
        self.execute("SET_CONTEXT", {"context": "chrome"})
        self.execute_script(
            """
            Services.prefs.setStringPref('browser.download.dir', arguments[0]);
            """, path)
        self.execute("SET_CONTEXT", {"context": "content"})
        self.download_path = path

    def getDownLoadedFileName(self):
        """Gets the filename of the most recently downloaded file."""
        self.get("about:downloads")
        try:
            downloads = WebDriverWait(self, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, "downloadTarget")))
        except TimeoutException:
            raise NoRecentDownloadError("There were no downloaded files.")

        filename = downloads[0].get_attribute('value')
        return filename

    def export_sds(
            self,
            download_path: str = ".",
            download_wait: int = 1200,  # 20 minutes
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
            download_path: The directory to save the export.
            download_wait: Optional; the amount of time to wait for Compass to 
                generate the export, default 10 mins.
            append_date: If True, append today's date to the filenames in
                yyyy-mm-dd format.
        '''
        download_path = os.path.normpath(download_path)
        self.set_download_dir(download_path)

        # download Microsoft SDS export
        self.get("https://" + self.school_code +
                 ".compass.education/Learn/Subjects.aspx")
        # Export menu
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Exports')]"))).click()
        # Export menu item
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(text(),'Microsoft SDS Export')]"))).click()
        # Submit button
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Download')]"))).click()
        # Yes button
        WebDriverWait(self, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'OK')]"))).click()

        # Poll to see when download is done
        for _i in range(download_wait):
            time.sleep(1)
            try:
                # Get cancel button
                button = self.find_element_by_xpath(
                    "//*[contains(text(),'Cancel')]")
            except NoSuchElementException:
                close_buttons = self.find_elements_by_xpath(
                    "//span[contains(text(),'Close')]")
                close_buttons[-1].click()
                break

        filename = self.getDownLoadedFileName()
        file_to_extract = os.path.join(download_path, filename)
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
                    zip_ref.extract(content, path=download_path)
        os.remove(file_to_extract)

    def export_student_details(self,
                               download_path: str = "student details.csv",
                               detailed: bool = False) -> None:
        '''Exports student details from Compass.

        The basic export includes student codes, name, gender, year level and
        form group. It only includes current students.
        The detailed export also includes DOB, VCAA code, VSN, and school 
        house. It includes students who have exited.

        Args:
            download_path: The file path to save the csv export, including filename.
            detailed: Whether to perform a detailed student details export.
        '''
        headers = {
            "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0"
        }
        s = requests.session()
        s.headers.update(headers)
        # copy cookies from selenium session
        for cookie in self.get_cookies():
            c = {cookie['name']: cookie['value']}
            s.cookies.update(c)
        # request student details file
        if detailed:
            url = f"https://{self.school_code}.compass.education/Services/FileDownload/CsvRequestHandler?type=37"
        else:
            url = f"https://{self.school_code}.compass.education/Services/FileDownload/CsvRequestHandler?type=38"
        r = s.get(url)
        with open(download_path, "wb") as f:
            f.write(r.content)

    def export_student_household_information(self,
                               download_path: str = "student household information.csv") -> None:
        '''Exports student household information from Compass.

        The basic export includes student address, parent names and parent contact details.

        Args:
            download_path: The file path to save the csv export, including filename.
        '''
        headers = {
            "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0"
        }
        s = requests.session()
        s.headers.update(headers)
        # copy cookies from selenium session
        for cookie in self.get_cookies():
            c = {cookie['name']: cookie['value']}
            s.cookies.update(c)
        # request student details file
        url = f"https://{self.school_code}.compass.education/Services/FileDownload/CsvRequestHandler?type=14"
        r = s.get(url)
        with open(download_path, "wb") as f:
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
        reports_tabs = self.execute_script("""
            return Array.prototype.slice.call(document.getElementsByClassName("x-tab"))
                .filter(function (x) { return x.textContent === "Reports"; });
            """)
        if len(reports_tabs) == 1:
            reports_tabs[0].click()
        else:
            raise CompassElementSelectionError("Could not select Reports tab.")
        # Open dropdown menu
        panel_element = WebDriverWait(self, 20).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//span[contains(text(),'Academic Year Export (CSV)')]/../../../../../.."
            )))  #menu panel
        panel_element.find_element_by_class_name(
            'x-form-trigger').click()  # dropdown menu

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
        reports_tabs = self.execute_script("""
            return Array.prototype.slice.call(document.getElementsByClassName("x-tab"))
                .filter(function (x) { return x.textContent === "Reports"; });
            """)
        if len(reports_tabs) == 1:
            reports_tabs[0].click()
        else:
            raise CompassElementSelectionError("Could not select Reports tab.")

        # Open dropdown menu
        panel_element = WebDriverWait(self, 20).until(
            EC.presence_of_element_located((
                By.XPATH,
                "//span[contains(text(),'Academic Year Export (CSV)')]/../../../../../.."
            )))  #menu panel
        panel_element.find_element_by_class_name(
            'x-form-trigger').click()  # dropdown menu

        # select the academic year
        menu_items = self.execute_script("""
            return Array.prototype.slice.call(document.getElementsByClassName("x-boundlist-item"))
                .filter(function (x) { return x.textContent === '""" +
                                         academic_year + """'; });
            """)
        if len(menu_items) == 1:
            menu_items[0].click()
        else:
            raise CompassElementSelectionError(
                f"Could not select academic year '{academic_year}' from menu.")

        # Press export button
        panel_element.find_element_by_xpath("//span[text()='Export']").click()
        # Confirm OK
        alert_window = WebDriverWait(self, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "x-window")))
        alert_window.find_element_by_xpath(
            "//span[text()='OK']").click()  # OK button
        for _i in range(1200):  # 20 minutes
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
                                        published_only: bool = True
                                       ) -> list(str):
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
            elements = WebDriverWait(self, 20).until(
                EC.presence_of_all_elements_located((
                    By.XPATH,
                    "//table/tbody/tr/td/div[contains(text(),'Published To All')]/parent::*/parent::*/child::td[1]/div/a"
                )))
        else:
            elements = WebDriverWait(self, 20).until(
                EC.presence_of_all_elements_located((
                    By.XPATH,
                    "//table/tbody/tr/td/div/parent::*/parent::*/child::td[1]/div/a"
                )))

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
                (By.XPATH,
                 "//a/span/span/span[contains(text(),'OK')]"))).click()
        for _i in range(1200):  # 20 minutes
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
            A list of the (year,name) pairs for each report cyle.
        """
        # open reports page
        self.get("https://" + self.school_code +
                 ".compass.education/Organise/Reporting/Cycles.aspx")
        rows = WebDriverWait(self, 20).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//div/div[3]/div/table/tbody/tr")))
        rows = self.find_elements_by_xpath("//div/div[3]/div/table/tbody/tr")
        cycles = []
        for row in rows:
            published_to_students = row.find_element_by_xpath("./td[5]").text
            report_style = row.find_element_by_xpath("./td[3]").text
            if ((not published_only) or
                (published_to_students == "Yes")) and (report_style
                                                       == "Writer"):
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
        try:
            previous_download = self.getDownLoadedFileName()
        except NoRecentDownloadError:
            previous_download = None

        self.get("https://" + self.school_code +
                 ".compass.education/Organise/Reporting/Cycles.aspx")
        # open cycle config page
        rows = WebDriverWait(self, 20).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, "//div/div[3]/div/table/tbody/tr")))
        for row in rows:
            row_year = row.find_element_by_xpath("./td[1]").text
            row_title = row.find_element_by_xpath("./td[2]").text
            if (row_year == year) and (row_title == title):
                try:
                    row.find_element_by_xpath("./td[2]/div/a").click()
                except NoSuchElementException:
                    return
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
                (By.XPATH,
                 "//a/span/span/span[contains(text(),'OK')]"))).click()
        # wait for download
        for _i in range(1200):  # 20 minutes
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
        file_name = self.getDownLoadedFileName()
        #TODO: Consider clearing browser download history. Would required
        # deleting from places.sqlite in profile folder.
        # Profile folder can be found using driver.capabilities['moz:profile']
        if file_name != previous_download:  # confirm a new file was actually downloaded
            source_path = os.path.join(download_path, file_name)
            rename_path = os.path.join(download_path,
                                       f"SemesterReports-{year}-{title}.csv")
            if os.path.exists(rename_path):
                os.remove(rename_path)
            os.rename(source_path, rename_path)
        else:
            raise CompassDownloadFailedError(
                f"Download of reports for Year:{year} and Title:{title} failed."
            )


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


class CompassFirefoxCookieAuthenticator(CompassAuthenticator):
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


class CompassElementSelectionError(Exception):
    """Raised when an expected user interface element is not found."""
    pass


class NoRecentDownloadError(Exception):
    """Raised if there is no most recent download to return."""
    pass


class CompassDownloadFailedError(Exception):
    """Raised a Compass download fails for some reason."""
    pass
