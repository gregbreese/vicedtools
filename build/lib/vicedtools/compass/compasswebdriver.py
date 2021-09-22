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
from typing import Protocol

import browser_cookie3
from selenium import webdriver


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
        for c in cj:
            cookie_dict = {
                'name': c.name,
                'value': c.value,
                'domain': c.domain,
                'expires': c.expires,
                'path': c.path
            }
            driver.add_cookie(cookie_dict)
