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

import browser_cookie3

from vicedtools.compass import CompassAuthenticator, CompassSession


class CompassFirefoxCookieAuthenticator(CompassAuthenticator):
    """A Compass authenaticator that gets login details from the local Firefox installation."""

    def authenticate(self, s: CompassSession):
        cj = browser_cookie3.firefox(
            domain_name=f'{s.school_code}.compass.education')

        for cookie in cj:
            c = {cookie.name: cookie.value}
            s.cookies.update(c)
