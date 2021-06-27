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

import glob
import os
import requests
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import zipfile


# Todo: provide additional login options, including grabbing cookies from an
#   existing Firefox profile and from environment variables.
def sds_export(download_path: str,
               geckodriver_path: str,
               compass_school_code: str,
               download_wait: int = 10 * 60) -> None:
    '''Exports class enrolment and teacher information from Compass.

    Downloads the Microsoft SDS export from Compass using Selenium and the
    Firefox webdriver.

    Will prompt for Compass login details.
    Requires access to SDS Export rights in the Subjects and Classes page.

    Will save four files in the provided path:
        StudentEnrollment.csv: contains student->class mappings
        Teacher.csv: contains teacher id information
        TeacherRoster.csv: contains teacher->class mappings
        Section.csv: contains class id information

    Args:
        download_path: The directory to save the export. Must use \\ slashes in 
                        windows.
        geckodriver_path: The location of geckodriver.exe
        compass_school_code: Your Compass school code.
        download_wait: Optional; the amount of time to wait for Compass to 
            generate the export, default 10 mins.
    '''
    # create Firefox profile
    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", download_path)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv, application/zip")

    #load web driver
    driver = webdriver.Firefox(executable_path=geckodriver_path,
                               firefox_profile=profile)

    #login to compass
    driver.get("https://" + compass_school_code + ".compass.education/")
    username_field = driver.find_element_by_name("username")
    username = input("Compass username: ")
    username_field.send_keys(username)
    password_field = driver.find_element_by_name("password")
    password = input("Compass password: ")
    password_field.send_keys(password)
    submit_button = driver.find_element_by_name("button1")
    submit_button.click()

    # download Microsoft SDS export
    driver.get("https://" + compass_school_code +
               ".compass.education/Learn/Subjects.aspx")
    time.sleep(3)
    export_menu = driver.find_element_by_id("button-1020")
    export_menu.click()
    time.sleep(3)
    export_menu = driver.find_element_by_id("menuitem-1025-itemEl")
    export_menu.click()
    time.sleep(3)
    submit_button = driver.find_element_by_id("button-1103")
    submit_button.click()
    time.sleep(3)
    yes_button = driver.find_element_by_id("button-1120")
    yes_button.click()
    time.sleep(download_wait)
    driver.quit()

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
    with zipfile.ZipFile(file_to_extract, 'r') as zip_ref:
        zip_ref.extract("StudentEnrollment.csv", path=download_path)
        zip_ref.extract("Teacher.csv", path=download_path)
        zip_ref.extract("TeacherRoster.csv", path=download_path)
        zip_ref.extract("Section.csv", path=download_path)
    os.remove(file_to_extract)


def export_student_details(download_path: str,
                           compass_school_code: str,
                           auth: str,
                           geckodriver_path: str = "") -> None:
    '''Exports student details from Compass.

    Args:
        download_path: The file path to save the csv export.
        compass_school_code: Your Compass school code.
        auth: 'selenium', 'browser_cookie3'
            The method for getting authentication cookies for Compass.
            browser_cookie3: uses locally stored cookies from Firefox
            selenium: will prompt for Compass login details, log into
                Compass, and then extract auth cookies.
        geckodriver_path: The location of geckodriver.exe, only required 
            if auth='selenium'
    '''
    if auth == 'browser_cookie3':
        import browser_cookie3
        cj = browser_cookie3.firefox(domain_name='compass.education')
        url = (
            "https://" + compass_school_code +
            ".compass.education/Services/FileDownload/CsvRequestHandler?type=37"
        )
        r = requests.get(url, cookies=cj)
    elif auth == 'selenium':
        from selenium import webdriver
        #load web driver
        driver = webdriver.Firefox(executable_path=geckodriver_path)
        #login to compass
        driver.get("https://" + compass_school_code + ".compass.education/")
        username_field = driver.find_element_by_name("username")
        username = input("Compass username: ")
        username_field.send_keys(username)
        password_field = driver.find_element_by_name("password")
        password = input("Compass password: ")
        password_field.send_keys(password)
        submit_button = driver.find_element_by_name("button1")
        submit_button.click()
        headers = {
            "User-Agent":
                "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"
        }
        s = requests.session()
        s.headers.update(headers)
        # copy cookies from selenium session
        for cookie in driver.get_cookies():
            c = {cookie['name']: cookie['value']}
            s.cookies.update(c)
        # request student details file
        r = s.get(
            "https://" + compass_school_code +
            ".compass.education/Services/FileDownload/CsvRequestHandler?type=38"
        )
    else:
        raise ValueError("Unrecognised auth method " + auth)

    with open(download_path, "xb") as f:
        f.write(r.content)


def exportLearningTasks(download_path: str, geckodriver_path: str,
                        compass_school_code: str, academic_year: str) -> None:
    """Exports all learning tasks data from Compass.
    
    Downloads the Learning Tasks exports from Compass using Selenium and the
    Firefox webdriver.

    Will prompt for Compass login details.
    Requires access to Learning Tasks Administration.

    Args:
        download_path: The directory to save the export. Must use \\ slashes in 
                        windows.
        geckodriver_path: The location of geckodriver.exe
        compass_school_code: Your Compass school code.
        academic_year: Which Compass academic year to download the export for.
            Use 'all' to download all available years.
    """

    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", download_path)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv, application/zip")

    #load web driver
    driver = webdriver.Firefox(executable_path=geckodriver_path,
                               firefox_profile=profile)

    #login to compass
    driver.get("https://" + compass_school_code + ".compass.education/")
    username_field = driver.find_element_by_name("username")
    username = input("Compass username: ")
    username_field.send_keys(username)
    password_field = driver.find_element_by_name("password")
    password = input("Compass password: ")
    password_field.send_keys(password)
    submit_button = driver.find_element_by_name("button1")
    submit_button.click()

    driver.get(
        "https://" + compass_school_code +
        ".compass.education/Communicate/LearningTasksAdministration.aspx")
    # Open Reports tab
    button = driver.find_element_by_id("tab-1101-btnIconEl")
    button.click()
    # Open dropdown menu
    button = driver.find_element_by_id("ext-gen1188")
    button.click()
    # Get dropdown menu items
    items = driver.find_elements_by_class_name("x-boundlist-item")
    academic_years = [item.text for item in items]
    if academic_year == all:
        for year in academic_years:
            # select the academic year
            button = driver.find_element_by_xpath("//*[contains(text(),'" +
                                                  year + "')]")
            button.click()
            # Press export button
            button = driver.find_element_by_id("button-1061-btnInnerEl")
            button.click()
            for _i in range(600):  # 10 minutes
                time.sleep(1)
                try:
                    # Get cancel button
                    button = driver.find_element_by_xpath(
                        "//*[contains(text(),'Cancel')]")
                    # Get 'Generating' banner
                    #banner = driver.find_element_by_xpath("//*[contains(text(),'Generating')]")
                except NoSuchElementException:
                    button = driver.find_element_by_xpath(
                        "//*[contains(text(),'Close')]")
                    button.click()
                    break
    elif academic_year in academic_years:
        # select the academic year
        button = driver.find_element_by_xpath("//*[contains(text(),'" + academic_year +
                                              "')]")
        button.click()
        # Press export button
        button = driver.find_element_by_id("button-1061-btnInnerEl")
        button.click()
        for _i in range(600):  # 10 minutes
            time.sleep(1)
            try:
                # Get cancel button
                button = driver.find_element_by_xpath(
                    "//*[contains(text(),'Cancel')]")
                # Get 'Generating' banner
                #banner = driver.find_element_by_xpath("//*[contains(text(),'Generating')]")
            except NoSuchElementException:
                button = driver.find_element_by_xpath(
                    "//*[contains(text(),'Close')]")
                button.click()
                break
    else:
        print("Academic year '" + academic_year + "' not found.")

    driver.close()


def exportProgressReports(download_path: str, geckodriver_path: str,
                        compass_school_code: str, cycle: str) -> None:
    """Export progress report data."""

    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", download_path)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv, application/zip")

    #load web driver
    driver = webdriver.Firefox(executable_path=geckodriver_path,
                            firefox_profile=profile)
    #login to compass
    driver.get("https://" + compass_school_code + ".compass.education/")
    username_field = driver.find_element_by_name("username")
    username = input("Compass username: ")
    username_field.send_keys(username)
    password_field = driver.find_element_by_name("password")
    password = input("Compass password: ")
    password_field.send_keys(password)
    submit_button = driver.find_element_by_name("button1")
    submit_button.click()

    # open progress reports page
    driver.get("https://" + compass_school_code + ".compass.education/Organise/Reporting/GPA/Default.aspx")
    # open cycles tab
    button = driver.find_element_by_xpath("//*[contains(text(),'Cycles')]")
    button.click()
    # all published progress reports
    progress_report_cycles = [e.text for e in driver.find_elements_by_xpath("//table/tbody/tr/td/div[contains(text(),'Published To All')]/parent::*/parent::*/child::td[1]/div/a")]

    if cycle == 'all':
        for this_cycle in progress_report_cycles:
            link = driver.find_element_by_xpath("//td/div/a[contains(text(), '" + this_cycle + "')]")
            link.click()

            # export link
            link = driver.find_element_by_link_text("Export results to CSV")
            link.click()

            button = driver.find_element_by_xpath("//a/span/span/span[contains(text(),'Export')]")
            button.click()

            button = driver.find_element_by_xpath("//a/span/span/span[contains(text(),'OK')]")
            button.click()

            try:
                # Get cancel button
                button = driver.find_element_by_xpath("//*[contains(text(),'Cancel')]")
                # Get 'Generating' banner
                banner = driver.find_element_by_xpath("//*[contains(text(),'Generating')]")
            except NoSuchElementException:
                button = driver.find_element_by_xpath("//*[contains(text(),'Close')]")
                button.click()

        # back to progres reports page
        link = driver.find_element_by_link_text("Back to Progress Reports")
        link.click()
        # open cycles tab
        button = driver.find_element_by_xpath("//*[contains(text(),'Cycles')]")
        button.click()
    elif cycle in progress_report_cycles:
        link = driver.find_element_by_xpath("//td/div/a[contains(text(), '" + cycle + "')]")
        link.click()

        # export link
        link = driver.find_element_by_link_text("Export results to CSV")
        link.click()

        button = driver.find_element_by_xpath("//a/span/span/span[contains(text(),'Export')]")
        button.click()

        button = driver.find_element_by_xpath("//a/span/span/span[contains(text(),'OK')]")
        button.click()

        try:
            # Get cancel button
            button = driver.find_element_by_xpath("//*[contains(text(),'Cancel')]")
            # Get 'Generating' banner
            banner = driver.find_element_by_xpath("//*[contains(text(),'Generating')]")
        except NoSuchElementException:
            button = driver.find_element_by_xpath("//*[contains(text(),'Close')]")
            button.click()
    else:
        print("Progress report cycle '" + cycle + "' not found.")

    driver.close()