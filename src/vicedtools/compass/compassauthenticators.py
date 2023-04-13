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

from __future__ import annotations

from abc import abstractmethod
import re
from typing import Protocol, TYPE_CHECKING
from urllib.parse import quote

if TYPE_CHECKING:
    from vicedtools.compass import CompassSession


class CompassAuthenticator(Protocol):
    """An abstract class for generic Compass authenticators."""

    @abstractmethod
    def authenticate(self, session: CompassSession):
        raise NotImplementedError


class CompassAuthenticationError(Exception):
    """Authentication with Compass failed."""
    pass


class CompassBasicAuthenticator(CompassAuthenticator):
    """Authenticates using a provided username and password."""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def authenticate(self, s: CompassSession):
        home_url = f"https://{s.school_code}.compass.education"
        r = s.get(home_url)
        # get viewstate
        pattern = 'id="__VIEWSTATE" value="(?P<viewstate>[0-9A-Za-z+/=]*)"'
        m = re.search(pattern, r.text)
        viewstate = quote(m.group('viewstate'))
        pattern = 'id="__VIEWSTATEGENERATOR" value="(?P<viewstategenerator>[0-9A-Za-z+/=]*)"'
        m = re.search(pattern, r.text)
        viewstategenerator = quote(m.group('viewstategenerator'))
        # url encode username and password
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        s.headers.update(headers)
        username = quote(self.username)
        password = quote(self.password)
        # auth
        login_url = f"https://{s.school_code}.compass.education/login.aspx?sessionstate=disabled"
        payload = f'__EVENTTARGET=button1&__EVENTARGUMENT=&__VIEWSTATE={viewstate}&browserFingerprint=3597254041&username={username}&password={password}&g-recaptcha-response=&rememberMeChk=on&__VIEWSTATEGENERATOR={viewstategenerator}'
        r = s.post(login_url, data=payload)
        if r.status_code != 200:
            raise CompassAuthenticationError
        pattern = "Sorry - your username and/or password was incorrect"
        m = re.search(pattern, r.text)
        if m:
            raise CompassAuthenticationError


class CompassCLIAuthenticator(CompassAuthenticator):
    """Authenticates using login details from CLI prompt."""

    def authenticate(self, s: CompassSession):
        username = input("Compass username: ")
        password = input("Compass password: ")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        s.headers.update(headers)
        login_url = f"https://{s.school_code}.compass.education/login.aspx?sessionstate=disabled"
        # get viewstate
        r = s.get(login_url)
        pattern = 'id="__VIEWSTATE" value="(?P<viewstate>[0-9A-Za-z+/=]*)"'
        m = re.search(pattern, r.text)
        viewstate = quote(m.group('viewstate'))
        pattern = 'id="__VIEWSTATEGENERATOR" value="(?P<viewstategenerator>[0-9A-Za-z+/=]*)"'
        m = re.search(pattern, r.text)
        viewstategenerator = quote(m.group('viewstategenerator'))
        # url encode username and password
        username = quote(username)
        password = quote(password)
        # auth
        payload = f'__EVENTTARGET=button1&__EVENTARGUMENT=&__VIEWSTATE={viewstate}&browserFingerprint=3597254041&username={username}&password={password}&g-recaptcha-response=&rememberMeChk=on&__VIEWSTATEGENERATOR={viewstategenerator}'
        r = s.post(login_url, data=payload)
        if r.status_code != 200:
            raise CompassAuthenticationError
        pattern = "Sorry - your username and/or password was incorrect"
        m = re.search(pattern, r.text)
        if m:
            raise CompassAuthenticationError
