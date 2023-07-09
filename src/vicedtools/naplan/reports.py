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
"""Functions for creating reports from NAPLAN data"""

import glob
import json
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tools import add_constant


def get_band(score: float, test: str) -> int:
    """Returns the NAPLAN band for a given test score.
    
    Args:
        score: The naplan scale score as a float as given in the READING_nb,
        WRITING_nb, etc fields of the NAPLAN outcomes csv.
        test: The naplan test code as given in the Reporting Test field of the
            NAPLAN outcomes csv. E.g. "YR7P"

    Returns:
        The NAPLAN band as an integer.
    """
    year_level = int(test[2])
    if score < 270 and year_level == 3:
        return 1
    elif score < 322 and year_level == 3:
        return 2
    elif score < 374 and year_level <= 5:
        return 3
    elif score < 426 and year_level <= 7:
        return 4
    elif score < 478:
        return 5
    elif score < 530 or year_level == 3:
        return 6
    elif score < 582:
        return 7
    elif score < 634 or year_level == 5:
        return 8
    elif score < 686 or year_level == 7:
        return 9
    else:
        return 10


def is_in_top_two_bands(band: int, test: str) -> bool:
    """Returns True if the given band is in the top two bands for a given test.
    
    Args:
        band: The NAPLAN band as an integer.
        test: The naplan test code as given in the Reporting Test field of the
            NAPLAN outcomes csv. E.g. "YR7P"

    Returns:
        True if the given band is in the top two bands. 
    """
    year_level = int(test[2])
    return ((year_level == 3 and band >= 5) or
            (year_level == 5 and band >= 7) or
            (year_level == 7 and band >= 8) or (year_level == 9 and band >= 9))


def is_in_bottom_two_bands(band, test):
    """Returns True if the band is in the bottom two bands for a given test.
    
    Args:
        band: The NAPLAN band as an integer.
        test: The naplan test code as given in the Reporting Test field of the
            NAPLAN outcomes csv. E.g. "YR7P"

    Returns:
        True if the given band is in the bottom two bands.
    """
    year_level = int(test[2])
    return ((year_level == 3 and band <= 2) or
            (year_level == 5 and band <= 4) or
            (year_level == 7 and band <= 5) or (year_level == 9 and band <= 6))


def create_outcome_summary(naplan_outcomes_dir: str,
                           naplan_outcomes_combined_csv: str):
    """Combines NAPLAN outcomes exports into a single summary.
    
    Combines all outcomes CSV exports from a given directory into a single
    file. Expects outcomes exports to include "Outcome" in their file name.
    Adds additional columns with the student's band for each test and
    whether the student's result was in the top two or bottom two bands.

    Args:
        naplan_outcomes_dir: The folder to search for CSV files.
        naplan_outcomes_combined_csv: The path to save the summary to.
    """
    filenames = glob.glob(f"{naplan_outcomes_dir}/*Outcome*.csv")
    outcomes_dfs = []
    for filename in filenames:
        temp_df = pd.read_csv(filename, dtype='str')
        outcomes_dfs.append(temp_df)

    outcomes_df = pd.concat(outcomes_dfs)
    outcomes_df.columns = [c.strip() for c in outcomes_df.columns]

    fields = [
        "READING", "WRITING", "SPELLING", "NUMERACY", "GRAMMAR & PUNCTUATION"
    ]
    for field in fields:
        outcomes_df[f"{field}_nb"] = outcomes_df[f"{field}_nb"].astype(float)
        outcomes_df[f"{field}_band"] = outcomes_df.apply(
            lambda x: get_band(x[f"{field}_nb"], x["Reporting Test"]), axis=1)
        outcomes_df[f"{field}_toptwo"] = outcomes_df.apply(
            lambda x: is_in_top_two_bands(x[f"{field}_band"], x["Reporting Test"
                                                               ]),
            axis=1)
        outcomes_df[f"{field}_bottomtwo"] = outcomes_df.apply(
            lambda x: is_in_bottom_two_bands(x[f"{field}_band"], x[
                "Reporting Test"]),
            axis=1)

    column_order = [
        'APS Year', 'Reporting Test', 'Cases ID', 'First Name', 'Second Name',
        'Surname', 'READING_nb', 'READING_band', 'READING_toptwo',
        'READING_bottomtwo', 'WRITING_nb', 'WRITING_band', 'WRITING_toptwo',
        'WRITING_bottomtwo', 'SPELLING_nb', 'SPELLING_band', 'SPELLING_toptwo',
        'SPELLING_bottomtwo', 'NUMERACY_nb', 'NUMERACY_band', 'NUMERACY_toptwo',
        'NUMERACY_bottomtwo', 'GRAMMAR & PUNCTUATION_nb',
        'GRAMMAR & PUNCTUATION_band', 'GRAMMAR & PUNCTUATION_toptwo',
        'GRAMMAR & PUNCTUATION_bottomtwo'
    ]

    outcomes_df[column_order].to_csv(naplan_outcomes_combined_csv)


def extract_summaries_from_sssr(sssr_data_js: str, destination_dir: str):
    """Extracts test metadata and an item analysis from the SSSR data.js.
    
    Extracts the following data from the SSSR:
    * Band cutoffs saved as bands.csv
    * Domain and sub-domain metadata saved as domains.csv and subdomains.csv
    * Question metadata saved as questions.csv
    * An item analysis for each question saved as "question summary.csv"

    Args:
        sssr_data_js: The path to the SSSR data.js file.
        destination_dir: The path to save all exports to.
    """
    with open(sssr_data_js, 'r', encoding='utf8') as f:
        data = f.readline()
    results = json.loads(data[11:])

    extracted_attempts = np.concatenate(
        [extract_attempt_details(attempt) for attempt in results['attempts']])
    responses_df = pd.DataFrame.from_records(extracted_attempts)
    del extracted_attempts

    # extract test metadata
    domains_df = pd.DataFrame(results['domains'])
    domains_df.set_index("domainId", inplace=True)
    domain_csv = os.path.join(destination_dir, "domains.csv")
    domains_df.to_csv(domain_csv, index=False)
    subdomains_df = pd.DataFrame(results['subdomains'])
    subdomains_df.set_index("domainId", inplace=True)
    subdomains_csv = os.path.join(destination_dir, "subdomains.csv")
    subdomains_df.to_csv(subdomains_csv, index=False)
    questions_df = pd.DataFrame(results['questions'])
    questions_df.set_index("questionId", inplace=True)
    questions_df[
        "exemplarItemImageURL"] = "https://exemplars.nap.edu.au/exemplars/NAPLAN/" + questions_df[
            "exemplarItem"].str[-9:] + ".png"
    questions_df["exemplarItemImageFile"] = questions_df["exemplarItem"].str[
        -9:] + ".png"
    questions_csv = os.path.join(destination_dir, "questions.csv")
    questions_df.to_csv(questions_csv, index=False)

    disciplineId_to_domainName = responses_df[['domainName', 'disciplineId'
                                              ]].drop_duplicates()
    bands_df = extract_bands_info(results)
    bands_df = bands_df.merge(disciplineId_to_domainName, on='disciplineId')
    bands_csv = os.path.join(destination_dir, "bands.csv")
    bands_df.to_csv(bands_csv, index=False)

    responses_df = pd.merge(responses_df,
                            questions_df[["eventIdentifier", "difficulty"]],
                            on=["questionId", "eventIdentifier"])
    responses_df["scaledScore"] = responses_df["scaledScore"].astype(float)
    responses_df[
        'scaleDelta'] = responses_df['scaledScore'] - responses_df["difficulty"]
    responses_df['correctScore'] = responses_df['correct'].apply(lambda a: 1
                                                                 if a else 0)

    # estimate item difficulties by fitting a logistic regression
    REF_PARAMS = {}
    REF_COV_PARAMS = {}
    for domain in [
            "Numeracy", "Reading", "Spelling", "Grammar and Punctuation"
    ]:  #
        selected_responses = responses_df[responses_df["domainName"] == domain]
        X = selected_responses["scaleDelta"].values.reshape(-1, 1)
        y = selected_responses["correctScore"]
        model = sm.Logit(y, add_constant(X)).fit(disp=False)
        REF_PARAMS[domain] = model.params.values
        REF_COV_PARAMS[domain] = model.cov_params()
    ref_params = [(a[0], a[1][0], a[1][1]) for a in REF_PARAMS.items()]
    ref_params = pd.DataFrame.from_records(
        ref_params, columns=["domainName", "intercept", "x1"])
    responses_df = responses_df.merge(ref_params, on="domainName")
    # predict scores from estimated item difficulties and student scores
    responses_df['expectedScore'] = 1 / (
        1 + np.exp(-(responses_df['x1'] * responses_df['scaleDelta'] +
                     responses_df['intercept'])))
    responses_df['scoreError'] = responses_df['correctScore'] - responses_df[
        'expectedScore']

    # aggregate item data to create question summary
    records = []
    for question_id in questions_df[questions_df["domain"] !=
                                    "Writing"].index.unique():
        selected_responses = responses_df[responses_df["questionId"] ==
                                          question_id].copy()
        descriptor = questions_df.loc[[question_id], "descriptor"][0]
        domain = questions_df.loc[[question_id], "domain"][0]
        subdomain = questions_df.loc[[question_id], "subdomain"][0]
        difficulty = questions_df.loc[[question_id], "difficulty"][0]
        exemplar = questions_df.loc[[question_id], "exemplarItem"][0]

        tests = selected_responses["eventIdentifier"].unique()

        for test in tests:
            record = {}
            record["descriptor"] = descriptor
            record["domain"] = domain
            record["subdomain"] = subdomain
            record["questionId"] = question_id
            record["eventIdentifier"] = test
            record["difficulty"] = difficulty
            record["exemplarItem"] = exemplar

            test_responses = selected_responses[
                selected_responses["eventIdentifier"] == test]
            record['n'] = len(test_responses)

            record['percentage correct'] = test_responses['correctScore'].mean()
            record['expected mean'] = test_responses['expectedScore'].mean()
            record['score error'] = test_responses['scoreError'].mean()

            record["scaleDelta mean"] = test_responses[
                "scaleDelta"].values.mean()
            if record["scaleDelta mean"] < -50:
                record["difficultyCategory"] = "Harder question"
            elif record["scaleDelta mean"] < 50:
                record["difficultyCategory"] = "At-level question"
            else:
                record["difficultyCategory"] = "Easier question"

            records.append(record)

    question_summary_df = pd.DataFrame.from_records(records)
    del records

    columns = [
        'descriptor', 'domain', 'subdomain', 'difficulty', 'questionId',
        'eventIdentifier', 'n', 'difficultyCategory', 'percentage correct',
        'expected mean', 'score error', "exemplarItem"
    ]
    question_summary_csv = os.path.join(destination_dir, "question summary.csv")
    question_summary_df[columns].to_csv(question_summary_csv, index=False)


def extract_bands_info(results):
    bands = []
    for test_level in results['testLevelBandsInfo']:
        for discipline in results['testLevelBandsInfo'][test_level]:
            for band in results['testLevelBandsInfo'][test_level][discipline]:
                extract = dict()
                for key in [
                        'band', 'bandStartPoint', 'scoreCutPoint',
                        'disciplineId'
                ]:
                    extract[key] = band[key]
                bands.append(extract)
    df = pd.DataFrame.from_records(bands)
    return df.drop_duplicates()


def extract_attempt_details(attempt):
    eventIdentifier = attempt['eventIdentifier']
    studentId = attempt['student']['studentId']
    try:
        schoolStudentId = attempt['student']['metadata']['schoolStudentId']
    except KeyError:
        schoolStudentId = ""
    testLevel = attempt['student']['testLevel']
    domainName = attempt['domain']['domainName']
    scaledScore = attempt['scaledScore']
    disciplineId = attempt['disciplineId']
    extracted_answers = []
    for answer in attempt['answers']:
        extracted_answer = {
            'eventIdentifier': eventIdentifier,
            'studentId': studentId,
            'schoolStudentId': schoolStudentId,
            'testLevel': testLevel,
            'domainName': domainName,
            'scaledScore': attempt['scaledScore'],
            'disciplineId': attempt['disciplineId']
        }
        for key in [
                'correct', 'questionNo', 'questionId', 'questionIdentifier',
                'performance', 'writingResponse', 'markingSchemeComponents'
        ]:
            extracted_answer[key] = answer[key]
        extracted_answers.append(extracted_answer)
    return extracted_answers
