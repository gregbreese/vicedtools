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

from datetime import datetime
import glob
import os
import requests
import time

from selenium.common.exceptions import NoSuchElementException
import zipfile

from vicedtools.compass.compasswebdriver import CompassWebDriver

def export_sds(driver: CompassWebDriver,
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
        driver: A CompassWebDriver instance
        download_path: The directory to save the export. Must use \\ slashes in 
                        windows.
        download_wait: Optional; the amount of time to wait for Compass to 
            generate the export, default 10 mins.
        append_date: If True, append today's date to the filenames in
            yyyy-mm-dd format.
    '''
    driver.set_preference("browser.download.dir", download_path)

    # download Microsoft SDS export
    driver.get("https://" + driver.school_code +
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


def export_student_details(driver: CompassWebDriver,
                           download_path: str = "student details.csv") -> None:
    '''Exports student details from Compass.

    Args:
        driver: An instance of CompassWebDriver
        download_path: The file path to save the csv export, including filename.
    '''
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
        "https://" + driver.school_code +
        ".compass.education/Services/FileDownload/CsvRequestHandler?type=38")
    with open(download_path, "xb") as f:
        f.write(r.content)


def discover_academic_years(driver: CompassWebDriver) -> list(str):
    """Discovers the academic years that exist in Compass.
    
    Useful for downloading learning tasks.

    Args:
        driver: An instance of CompassWebDriver

    Returns:
        A list of the names of each academic year.
    """
    driver.get(
        "https://" + driver.school_code +
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
    return academic_years


def export_learning_tasks(driver: CompassWebDriver,
                        academic_year: str,
                        download_path: str = ".\\") -> None:
    """Exports all learning tasks data from Compass.
    
    Downloads the Learning Tasks exports from Compass using Selenium and the
    Firefox webdriver.

    Will prompt for Compass login details.
    Requires access to Learning Tasks Administration.

    Data is saved as "[download_path]/LearningTasks-[academic_year].csv".

    Args:
        driver: An instance of CompassWebDriver
        download_path: The directory to save the export. Must use \\ slashes in 
                        windows.
        academic_year: Which Compass academic year to download the export for.
    """
    driver.set_preference("browser.download.dir", download_path)
    driver.get(
        "https://" + driver.school_code +
        ".compass.education/Communicate/LearningTasksAdministration.aspx")
    # Open Reports tab
    button = driver.find_element_by_id("tab-1101-btnIconEl")
    button.click()
    # Open dropdown menu
    button = driver.find_element_by_id("ext-gen1188")
    button.click()
    # select the academic year
    button = driver.find_element_by_xpath("//*[contains(text(),'" +
                                          academic_year + "')]")
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
        except NoSuchElementException:
            button = driver.find_element_by_xpath(
                "//*[contains(text(),'Close')]")
            button.click()
            break


def discover_progress_report_cycles(driver: CompassWebDriver,
                                 published_only: bool = True) -> list(str):
    """Discovers the available progress report cycles.

    Args:
        driver: An instance of CompassWebDriver
        published_only: if true, only return those cycles set as "Published to 
            All".

    Returns:
        A list of the names of each progress report cyle.
    """
    # open progress reports page
    driver.get("https://" + driver.school_code +
               ".compass.education/Organise/Reporting/GPA/Default.aspx")
    # open cycles tab
    button = driver.find_element_by_xpath("//*[contains(text(),'Cycles')]")
    button.click()
    # all published progress reports
    if published_only:
        elements = driver.find_elements_by_xpath(
            "//table/tbody/tr/td/div[contains(text(),'Published To All')]/parent::*/parent::*/child::td[1]/div/a"
        )
    else:
        elements = driver.find_elements_by_xpath(
            "//table/tbody/tr/td/div/parent::*/parent::*/child::td[1]/div/a")
    progress_report_cycles = [e.text for e in elements]

    return progress_report_cycles


def export_progress_report(driver: CompassWebDriver,
                         cycle: str,
                         download_path: str = ".\\") -> None:
    """Export progress report data.
    
    Data is saved as "[download_path]/[cycle].csv"

    Args:
        driver: An instance of CompassWebDriver
        cycle: The name of the progress report cycle to export.
        download_path: The directory to save the export. Must use \\ slashes in 
                        windows.
    """
    driver.set_preference("browser.download.dir", download_path)
    # open progress reports page
    driver.get("https://" + driver.school_code +
               ".compass.education/Organise/Reporting/GPA/Default.aspx")
    # open cycles tab
    button = driver.find_element_by_xpath("//*[contains(text(),'Cycles')]")
    button.click()
    # open selected cycle
    link = driver.find_element_by_xpath("//td/div/a[contains(text(), '" +
                                        cycle + "')]")
    link.click()
    # export link
    link = driver.find_element_by_link_text("Export results to CSV")
    link.click()
    # Export button
    button = driver.find_element_by_xpath(
        "//a/span/span/span[contains(text(),'Export')]")
    button.click()
    # Confirmation OK button
    button = driver.find_element_by_xpath(
        "//a/span/span/span[contains(text(),'OK')]")
    button.click()

    for _i in range(600):  # 10 minutes
        time.sleep(1)
        try:
            # Get cancel button
            button = driver.find_element_by_xpath(
                "//*[contains(text(),'Cancel')]")
        except NoSuchElementException:
            button = driver.find_element_by_xpath(
                "//*[contains(text(),'Close')]")
            button.click()
            break


def discover_report_cycles(driver: CompassWebDriver,
                         published_only: bool = True) -> list(tuple(str)):
    """Discovers the available report cycles.

    Args:
        driver: An instance of CompassWebDriver
        published_only: if true, only return those cycles set to allow student 
            access.

    Returns:
        A list of the names of each report cyle.
    """
    # open reports page
    driver.get("https://" + driver.school_code +
               ".compass.education/Organise/Reporting/Cycles.aspx")

    rows = driver.find_elements_by_xpath("//div/div[3]/div/table/tbody/tr")
    cycles = []
    for row in rows:
        published_to_students = row.find_element_by_xpath("./td[5]").text
        if not published_only or published_to_students == "Yes":
            year = row.find_element_by_xpath("./td[1]").text
            name = row.find_element_by_xpath("./td[2]").text
            cycles.append((year, name))

    return cycles


def export_report_cycle(driver: CompassWebDriver,
                      year: str,
                      title: str,
                      download_path: str = ".\\") -> None:
    """Export progress report data.
    
    Data is saved as "[download_path]/SemesterReportAllResultsCsvExport Generated - [%Y-%m-%d_%I%M%p].csv"

    Args:
        driver: An instance of CompassWebDriver
        year: The year of the report cycle to export.
        title: The title of the report cycle to export.
        download_path: The directory to save the export. Must use \\ slashes in 
                        windows.
    """
    driver.set_preference("browser.download.dir", download_path)

    driver.get("https://" + driver.school_code +
               ".compass.education/Organise/Reporting/Cycles.aspx")
    # open cycle config page
    rows = driver.find_elements_by_xpath("//div/div[3]/div/table/tbody/tr")
    for row in rows:
        row_year = row.find_element_by_xpath("./td[1]").text
        row_title = row.find_element_by_xpath("./td[2]").text
        if (row_year == year) and (row_title == title):
            row.find_element_by_xpath("./td[2]/div/a").click()
            break
    # export all results
    menu = driver.find_element_by_xpath("//*[@id='button-1076-btnWrap']")
    menu.click()
    all_results_item = driver.find_element_by_xpath(
        "//*[@id='menuitem-1084-textEl']")
    all_results_item.click()
    ok_button = driver.find_element_by_xpath(
        "//a/span/span/span[contains(text(),'OK')]")
    ok_button.click()
    # wait for download
    for _i in range(600):  # 10 minutes
        time.sleep(1)
        try:
            # Get cancel button
            button = driver.find_element_by_xpath(
                "//*[contains(text(),'Cancel')]")
        except NoSuchElementException:
            button = driver.find_element_by_xpath(
                "//*[contains(text(),'Close')]")
            button.click()
            break
