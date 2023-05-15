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

import pandas as pd
import pdfquery

def scrape_login_details(input_pdf, output_csv):
    """Scrapes the login details from the PDF given by DAL.

    Useful for mail merging login details to students instead of prining lots
    of slips of paper.

    Args:
        input_pdf: The location of the pdf containing the exported login
            details from DAL. Can be either the 1 per page or 14 per page
            exports.
        output_csv: The location to save the scraped data to.
    """
    pdf = pdfquery.PDFQuery(input_pdf)
    pdf.load()

    df = pd.DataFrame()
    # Extract classes
    es = pdf.tree.xpath("//*[contains(text(),'Class:')]")
    df["Class"] = [e.text[6:].strip() for e in es]
    # Extract student names
    es = pdf.tree.xpath("//*[contains(text(),'Name:')]")
    colon_position = es[0].text.find(":")
    df["Name"] = [e.text[colon_position + 1:].strip() for e in es]
    # Extract usernames
    es = pdf.tree.xpath("//*[contains(text(),'Username:')]")
    df["Username"] = [e.text[9:].strip() for e in es]
    # Extract passwords
    es = pdf.tree.xpath("//*[contains(text(),'Password:')]")
    df["Password"] = [e.text[9:].strip() for e in es]

    df["Instructions"] = """1. Enter dal.vcaa.vic.edu.au/student into your web browser.
    2. Type your username and password (shown above) into the boxes displayed on the browser then use the 'Login' button.
    """

    df.to_csv(output_csv, index=False)
