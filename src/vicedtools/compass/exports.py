# get a compass authentication cookie
from selenium import webdriver
import time
import requests
import urllib.request
import glob
import re
from datetime import datetime
import zipfile
import os


def export_student_enrolments(download_path,
                              geckodriver_path,
                              compass_school_code,
                              download_wait=10 * 60):
    '''Exports student enrolment information from Compass.

    Will prompt for Compass login details.
    Requires access to SDS Export rights in the Subjects and Classes page.

    Keyword arguments
    download_path: The directory to save the export. Must use \\ slashes in 
                    windows.
    geckodriver_path: The location of geckodriver.exe
    compass_school_code: Your Compass school code
    
    Optional keyword argumenbts
    download_wait: the amount of time to wait for Compass to generate the 
                    export, default 10 mins
    '''
    # create Firefox profile
    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", download_path)
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk",
                           "application/zip")

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
    os.remove(file_to_extract)


def export_student_details(download_path,
                           compass_school_code,
                           auth,
                           geckodriver_path=""):
    '''Exports student details from Compass.

    Keyword arguments:
    download_path: The file location to save the csv export.
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
        driver.get("https://gwsc-vic.compass.education/")
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
