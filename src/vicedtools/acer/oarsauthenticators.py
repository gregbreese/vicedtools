# Copyright 2023 VicEdTools authors

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Authenticator functions for the OARSSession class."""

from __future__ import annotations

from abc import abstractmethod
import re
from typing import Protocol, TYPE_CHECKING
from urllib.parse import quote

if TYPE_CHECKING:
    from vicedtools.oars import OARSSession


class OARSAuthenticator(Protocol):
    """An abstract class for generic OARS authenticators."""

    @abstractmethod
    def authenticate(self, session: OARSSession):
        raise NotImplementedError


class OARSBasicAuthenticator(OARSAuthenticator):
    """Authenticates using a provided username and password."""

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

    def authenticate(self, s: OARSSession):

        login_url = f"https://oars.acer.edu.au/{s.school}"
        # get security token
        r = s.get(login_url)
        pattern = r'name="security\[token\]" value="(?P<token>[\$0-9A-Za-z+/\.\\]*)"'
        m = re.search(pattern, r.text)
        security_token = quote(m.group('token'))
        # url encode username and password
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        s.headers.update(headers)
        username = quote(self.username)
        password = quote(self.password)
        # auth
        payload = f'security%5Btoken%5D={security_token}&username={username}&password={password}'
        r = s.post(login_url, data=payload)
        if r.status_code != 200:
            raise OARSAuthenticateError


class OARSAuthenticateError(Exception):
    """Raised if an error occurs related to OARS authentication."""
    pass
