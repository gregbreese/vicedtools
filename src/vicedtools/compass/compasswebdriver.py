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

import browser_cookie3
from selenium import webdriver

# TODO: implement auth from local environment variables/config file
# TODO: implement Chrome support
class CompassWebDriver(webdriver.Firefox):
    """WebDriver extension that stores the Compass school code."""

    def __init__(self,
                 school_code: str,
                 geckodriver_path: str,
                 download_path: str = "./",
                 auth: str = 'cli'):
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

        if auth == 'cli':
            #login to compass
            self.get("https://" + school_code + ".compass.education/")
            username_field = self.find_element_by_name("username")
            username = input("Compass username: ")
            username_field.send_keys(username)
            password_field = self.find_element_by_name("password")
            password = input("Compass password: ")
            password_field.send_keys(password)
            submit_button = self.find_element_by_name("button1")
            submit_button.click()
        elif auth == 'browser_cookie3':
            self.get("https://" + school_code + ".compass.education/")
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
                self.add_cookie(cookie_dict)
        else:
            raise ValueError("auth value '" + auth + "' not valid.")