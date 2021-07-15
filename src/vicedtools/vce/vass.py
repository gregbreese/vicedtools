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

import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

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
        self.driver = webdriver.Ie(executable_path=iedriver_path)

        self.launch_window = self.driver.current_window_handle
        # login to VASS
        self.driver.get("https://www.vass.vic.edu.au/login/")
        time.sleep(3)
        login_link = self.driver.find_element_by_name("boslogin")
        login_link.click()
        time.sleep(3)
        if auth == 'kwargs':
            # username/password
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.main_window = self.driver.current_window_handle
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