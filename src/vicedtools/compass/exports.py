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

import browser_cookie3
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import zipfile


# TODO: implement auth from local environment variables/config file
# TODO: implement Chrome support
def getCompassDriver(school_code: str,
                     geckodriver_path: str,
                     download_path: str = "./",
                     auth: str = 'cli') -> webdriver.Firefox:
    """Creates a webdriver with Compass authentication completed.
    
    Creates an instance of selenium.webdriver.Firefox and authenticates either
    through a manually entered username/password or through cookies stored in
    the locally installed Firefox installation.
    
    Args:
        school_code: Your school's compass school code.
        geckodriver_path: The path to geckodriver.exe
        download_path: The path to download any files to.
        auth: Either 'cli' or 'browser'. If 'cli' will request a username and
            password from the command line. If 'browser' will use cookies from
            the local Firefox installation.

    Returns:
        An instance of selenium.webdriver.Firefox with authentication to
        Compass completed.
    """
    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", download_path)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk",
                           "text/csv, application/zip")
    driver = webdriver.Firefox(executable_path=geckodriver_path,
                               firefox_profile=profile)
    if auth == 'cli':
        #login to compass
        driver.get("https://" + school_code + ".compass.education/")
        username_field = driver.find_element_by_name("username")
        username = input("Compass username: ")
        username_field.send_keys(username)
        password_field = driver.find_element_by_name("password")
        password = input("Compass password: ")
        password_field.send_keys(password)
        submit_button = driver.find_element_by_name("button1")
        submit_button.click()
        return driver
    elif auth == 'browser_cookie3':
        driver.get("https://" + school_code + ".compass.education/")
        cj = browser_cookie3.firefox(domain_name=school_code +
                                     '.compass.education')
        for c in cj:
            cookie_dict = {
                'name': c.name,
                'value': c.value,
                'domain': c.domain,
                'expires': c.expires,
                'path': c.path
            }
            driver.add_cookie(cookie_dict)
        return driver
    else:
        raise ValueError("auth value '" + auth + "' not valid.")


def sds_export(school_code: str,
               geckodriver_path: str,
               download_path: str = ".\\",
               auth='cli',
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
        school_code: Your Compass school code.
        geckodriver_path: The location of geckodriver.exe
        download_path: The directory to save the export. Must use \\ slashes in 
                        windows.
        auth: Either 'cli' or 'browser'. If 'cli' will request a username and
            password from the command line. If 'browser' will use cookies from
            the local Firefox installation.
        download_wait: Optional; the amount of time to wait for Compass to 
            generate the export, default 10 mins.
        append_date: If True, append today's date to the filenames in
            yyyy-mm-dd format.
    '''
    driver = getCompassDriver(school_code,
                              geckodriver_path,
                              download_path=download_path,
                              auth=auth)

    # download Microsoft SDS export
    driver.get("https://" + school_code +
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
                zip_ref.extract(file, path=download_path)
    os.remove(file_to_extract)


def export_student_details(school_code: str,
                           geckodriver_path: str = "",
                           download_path: str = "student details.csv",
                           auth: str = 'cli') -> None:
    '''Exports student details from Compass.

    Args:
        school_code: Your Compass school code.
        download_path: The file path to save the csv export, including filename.
        auth: Either 'cli' or 'browser'. If 'cli' then will open a
            browser window using Selenium and prompt for Compass login details
            from the command line. If 'browser' then will use cookies from the
            local Firefox installation.
        geckodriver_path: The location of geckodriver.exe, only required 
            if auth='selenium'
    '''
    if auth == 'browser':
        import browser_cookie3
        cj = browser_cookie3.firefox(domain_name='compass.education')
        url = (
            "https://" + school_code +
            ".compass.education/Services/FileDownload/CsvRequestHandler?type=37"
        )
        r = requests.get(url, cookies=cj)
    elif auth == 'cli':
        driver = getCompassDriver(school_code,
                                  geckodriver_path,
                                  download_path=download_path,
                                  auth='cli')
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
            "https://" + school_code +
            ".compass.education/Services/FileDownload/CsvRequestHandler?type=38"
        )
    else:
        raise ValueError("Unrecognised auth method " + auth)

    with open(download_path, "xb") as f:
        f.write(r.content)


def discoverAcademicYears(school_code: str,
                          geckodriver_path: str,
                          auth='cli') -> list(str):
    """Discovers the academic years that exist in Compass.
    
    Useful for downloading learning tasks.

    Args:
        compass_school_code: Your Compass school code.
        geckodriver_path: The location of geckodriver.exe
        auth: Either 'cli' or 'browser'. If 'cli' will request a username and
            password from the command line. If 'browser' will use cookies from
            the local Firefox installation.

    Returns:
        A list of the names of each academic year.
    """
    driver = getCompassDriver(school_code, geckodriver_path, auth=auth)
    driver.get(
        "https://" + school_code +
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
    driver.quit()
    return academic_years


def exportLearningTasks(school_code: str,
                        geckodriver_path: str,
                        download_path: str,
                        academic_year: str,
                        auth='cli') -> None:
    """Exports all learning tasks data from Compass.
    
    Downloads the Learning Tasks exports from Compass using Selenium and the
    Firefox webdriver.

    Will prompt for Compass login details.
    Requires access to Learning Tasks Administration.

    Data is saved as "[download_path]/LearningTasks-[academic_year].csv".

    Args:
        compass_school_code: Your Compass school code.
        geckodriver_path: The location of geckodriver.exe
        download_path: The directory to save the export. Must use \\ slashes in 
                        windows.
        academic_year: Which Compass academic year to download the export for.
        auth: Either 'cli' or 'browser'. If 'cli' will request a username and
            password from the command line. If 'browser' will use cookies from
            the local Firefox installation.
    """
    driver = getCompassDriver(school_code,
                              geckodriver_path,
                              download_path=download_path,
                              auth=auth)

    driver.get(
        "https://" + school_code +
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
    driver.quit()


def discoverProgressReportCycles(school_code: str,
                                 geckodriver_path: str,
                                 auth: str = 'cli',
                                 published_only: bool = True) -> list(str):
    """Discovers the available progress report cycles.

    Args:
        compass_school_code: Your Compass school code.
        geckodriver_path: The location of geckodriver.exe
        auth: Either 'cli' or 'browser'. If 'cli' will request a username and
            password from the command line. If 'browser' will use cookies from
            the local Firefox installation.
        published_only: if true, only return those cycles set as "Published to 
            All".

    Returns:
        A list of the names of each progress report cyle.
    """
    driver = getCompassDriver(school_code, geckodriver_path, auth=auth)
    # open progress reports page
    driver.get("https://" + school_code +
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
    driver.quit()
    return progress_report_cycles


def exportProgressReports(school_code: str,
                          geckodriver_path: str,
                          cycle: str,
                          download_path: str,
                          auth: str = 'cli') -> None:
    """Export progress report data.
    
    Data is saved as "[download_path]/[cycle].csv"

    Args:
        compass_school_code: Your Compass school code.
        geckodriver_path: The location of geckodriver.exe
        download_path: The directory to save the export. Must use \\ slashes in 
                        windows.
        cycle
        auth: Either 'cli' or 'browser'. If 'cli' will request a username and
            password from the command line. If 'browser' will use cookies from
            the local Firefox installation.
    """

    driver = getCompassDriver(school_code,
                              geckodriver_path,
                              download_path=download_path,
                              auth=auth)

    # open progress reports page
    driver.get("https://" + school_code +
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
    driver.quit()

def discoverReportCycles(school_code: str,
                                 geckodriver_path: str,
                                 auth: str = 'cli',
                                 published_only: bool = True) -> list(tuple(str)):
    """Discovers the available report cycles.

    Args:
        compass_school_code: Your Compass school code.
        geckodriver_path: The location of geckodriver.exe
        auth: Either 'cli' or 'browser'. If 'cli' will request a username and
            password from the command line. If 'browser' will use cookies from
            the local Firefox installation.
        published_only: if true, only return those cycles set to allow student 
            access.

    Returns:
        A list of the names of each report cyle.
    """
    driver = getCompassDriver(school_code, geckodriver_path, auth=auth)
    # open progress reports page
    driver.get("https://" + school_code +
               ".compass.education/Organise/Reporting/Cycles.aspx")

    rows = driver.find_elements_by_xpath("//div/div[3]/div/table/tbody/tr")
    cycles = []
    for row in rows:
        published_to_students = row.find_element_by_xpath("./td[5]").text
        if not published_only or published_to_students == "Yes":
            year = row.find_element_by_xpath("./td[1]").text
            name = row.find_element_by_xpath("./td[2]").text
            cycles.append( (year,name))

    driver.quit()
    return cycles
 