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

from google.cloud import bigquery

STUDENT_DETAILS_SCHEMA = [
    bigquery.SchemaField("StudentCode", "STRING"),
    bigquery.SchemaField("Surname", "STRING"),
    bigquery.SchemaField("FirstName", "STRING"),
    bigquery.SchemaField("PrefName", "STRING"),
    bigquery.SchemaField("Gender", "STRING"),
    bigquery.SchemaField("YearLevel", "STRING"),
    bigquery.SchemaField("HomeGroup", "STRING"),
    bigquery.SchemaField("Status", "STRING"),
    bigquery.SchemaField("DateOfBirth", "DATE")
]
STUDENT_DETAILS_CLUSTERING_FIELDS = [
    "Status", "StudentCode", "YearLevel", "Gender"
]

STUDENT_ENROLMENTS_SCHEMA = [
    bigquery.SchemaField("EnrolmentClassCode", "STRING"),
    bigquery.SchemaField("StudentCode", "STRING")
]

STUDENT_ENROLMENTS_CLUSTERING_FIELDS = ["EnrolmentClassCode", "StudentCode"]

REPORTS_SCHEMA = [
    bigquery.SchemaField("Time", "DATE"),
    bigquery.SchemaField("ClassCode", "STRING"),
    bigquery.SchemaField("StudentCode", "STRING"),
    bigquery.SchemaField("ResultName", "STRING"),
    bigquery.SchemaField("ResultGrade", "STRING"),
    bigquery.SchemaField("ResultScore", "FLOAT"),
    bigquery.SchemaField("Type", "STRING"),
    bigquery.SchemaField("SubjectName", "STRING"),
    bigquery.SchemaField("SubjectCode", "STRING"),
    bigquery.SchemaField("LearningArea", "STRING"),
    bigquery.SchemaField("TeacherCode", "STRING")
]
REPORTS_CLUSTERING_FIELDS = ["StudentCode", "Type", "LearningArea", "Time"]

REPORTS_SUMMARY_SCHEMA = [
    bigquery.SchemaField("Time", "DATE"),
    bigquery.SchemaField("ClassCode", "STRING"),
    bigquery.SchemaField("StudentCode", "STRING"),
    bigquery.SchemaField("SubjectCode", "STRING"),
    bigquery.SchemaField("SubjectName", "STRING"),
    bigquery.SchemaField("LearningArea", "STRING"),
    bigquery.SchemaField("TeacherCode", "STRING"),
    bigquery.SchemaField("Academic", "FLOAT"),
    bigquery.SchemaField("Work_Habits", "FLOAT"),
]
REPORTS_SUMMARY_CLUSTERING_FIELDS = [
    "StudentCode", "Time", "LearningArea", "TeacherCode"
]

NAPLAN_OUTCOMES_SCHEMA = [
    bigquery.SchemaField("APS_Year", "STRING"),
    bigquery.SchemaField("Reporting_Test", "STRING"),
    bigquery.SchemaField("Cases_ID", "STRING"),
    bigquery.SchemaField("First_Name", "STRING"),
    bigquery.SchemaField("Second_Name", "STRING"),
    bigquery.SchemaField("Surname", "STRING"),
    bigquery.SchemaField("READING_nb", "FLOAT"),
    bigquery.SchemaField("READING_band", "INTEGER"),
    bigquery.SchemaField("READING_toptwo", "BOOLEAN"),
    bigquery.SchemaField("READING_bottomtwo", "BOOLEAN"),
    bigquery.SchemaField("WRITING_nb", "FLOAT"),
    bigquery.SchemaField("WRITING_band", "INTEGER"),
    bigquery.SchemaField("WRITING_toptwo", "BOOLEAN"),
    bigquery.SchemaField("WRITING_bottomtwo", "BOOLEAN"),
    bigquery.SchemaField("SPELLING_nb", "FLOAT"),
    bigquery.SchemaField("SPELLING_band", "INTEGER"),
    bigquery.SchemaField("SPELLING_toptwo", "BOOLEAN"),
    bigquery.SchemaField("SPELLING_bottomtwo", "BOOLEAN"),
    bigquery.SchemaField("NUMERACY_nb", "FLOAT"),
    bigquery.SchemaField("NUMERACY_band", "INTEGER"),
    bigquery.SchemaField("NUMERACY_toptwo", "BOOLEAN"),
    bigquery.SchemaField("NUMERACY_bottomtwo", "BOOLEAN"),
    bigquery.SchemaField("GRAMMAR___PUNCTUATION_nb", "FLOAT"),
    bigquery.SchemaField("GRAMMAR___PUNCTUATION_band", "INTEGER"),
    bigquery.SchemaField("GRAMMAR___PUNCTUATION_toptwo", "BOOLEAN"),
    bigquery.SchemaField("GRAMMAR___PUNCTUATION_bottomtwo", "BOOLEAN"),
]

NAPLAN_OUTCOMES_CLUSTERING_FIELDS = [
    "APS_Year",
    "Reporting_Test",
    "Cases_ID",
]

NAPLAN_OUTCOMES_MOST_RECENT_CLUSTERING_FIELDS = [
    "Cases_ID",
]

GAT_SCHEMA = [
    bigquery.SchemaField("Year", "STRING"),
    bigquery.SchemaField("candNum", "STRING"),
    bigquery.SchemaField("Student_Name", "STRING"),
    bigquery.SchemaField("incomplete", "BOOLEAN"),
    bigquery.SchemaField("exempt", "BOOLEAN"),
    bigquery.SchemaField("CofD", "BOOLEAN"),
    bigquery.SchemaField("COM", "FLOAT"),
    bigquery.SchemaField("AHU", "FLOAT"),
    bigquery.SchemaField("MST", "FLOAT"),
    bigquery.SchemaField("stdCOM", "FLOAT"),
    bigquery.SchemaField("stdAHU", "FLOAT"),
    bigquery.SchemaField("stdMST", "FLOAT"),
]
GAT_CLUSTERING_FIELDS = ["candNum", "Year", "incomplete"]

PAT_SCORES_SCHEMA = [
    bigquery.SchemaField("StudentCode", "STRING"),
    bigquery.SchemaField("Date", "DATETIME"),
    bigquery.SchemaField("YearLevel", "STRING"),
    bigquery.SchemaField("Test", "STRING"),
    bigquery.SchemaField("TestForm", "STRING"),
    bigquery.SchemaField("Scale", "FLOAT"),
    bigquery.SchemaField("ScoreCategory", "STRING"),
]
PAT_SCORES_CLUSTERING_FIELDS = ["Test", "StudentCode", "Date", "YearLevel"]

PAT_MOST_RECENT_SCHEMA = [
    bigquery.SchemaField("StudentCode", "STRING"),
    bigquery.SchemaField("MathsDate", "DATETIME"),
    bigquery.SchemaField("ReadingDate", "DATETIME"),
    bigquery.SchemaField("MathsYearLevel", "STRING"),
    bigquery.SchemaField("ReadingYearLevel", "STRING"),
    bigquery.SchemaField("MathsTestForm", "STRING"),
    bigquery.SchemaField("ReadingTestForm", "STRING"),
    bigquery.SchemaField("MathsScale", "FLOAT"),
    bigquery.SchemaField("ReadingScale", "FLOAT"),
    bigquery.SchemaField("MathsScoreCategory", "STRING"),
    bigquery.SchemaField("ReadingScoreCategory", "STRING")
]
PAT_MOST_RECENT_CLUSTERING_FIELDS = ["StudentCode"]

EWRITE_SCORES_SCHEMA = [
    bigquery.SchemaField("Date", "DATETIME"),
    bigquery.SchemaField("StudentCode", "STRING"),
    bigquery.SchemaField("Year_level", "INTEGER"),
    bigquery.SchemaField("Effective_year_level", "INTEGER"),
    bigquery.SchemaField("Result_flag", "STRING"),
    bigquery.SchemaField("Score", "INTEGER"),
    bigquery.SchemaField("Scale", "INTEGER"),
    bigquery.SchemaField("Band", "INTEGER"),
    bigquery.SchemaField("Response", "STRING"),
]

EWRITE_SCORES_CLUSTERING_FIELDS = [
    'Result_flag', 'StudentCode', 'Effective_year_level', 'Date'
]

EWRITE_CRITERIA_SCHEMA = [
    bigquery.SchemaField("Date", "DATETIME"),
    bigquery.SchemaField("StudentCode", "STRING"),
    bigquery.SchemaField("Year_level", "INTEGER"),
    bigquery.SchemaField("Effective_year_level", "INTEGER"),
    bigquery.SchemaField("Criteria", "STRING"),
    bigquery.SchemaField("Score", "INTEGER"),
    bigquery.SchemaField("Scale", "FLOAT"),
]

EWRITE_CRITERIA_CLUSTERING_FIELDS = [
    'Criteria', 'StudentCode', 'Effective_year_level', 'Date'
]
