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
    bigquery.SchemaField("DateOfBirth","DATE")
]
STUDENT_DETAILS_CLUSTERING_FIELDS = [
    "Status", "StudentCode", "YearLevel", "Gender"
]

STUDENT_CLASS_RELATIONSHIPS_SCHEMA = [
    bigquery.SchemaField("ClassGroupCode", "STRING"),
    bigquery.SchemaField("StudentCode", "STRING")
    ]

STUDENT_CLASS_RELATIONSHIPS_CLUSTERING_FIELDS = [
    "ClassGroupCode", "StudentCode"
]

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
REPORTS_CLUSTERING_FIELDS = ["StudentCode", "Type", "LearningArea", "Time" ]

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

NAPLAN_SCHEMA = [
    bigquery.SchemaField("APS_Year", "STRING"),
    bigquery.SchemaField("Reporting_Test", "STRING"),
    bigquery.SchemaField("First_Name", "STRING"),
    bigquery.SchemaField("Second_Name", "STRING"),
    bigquery.SchemaField("Surname", "STRING"),
    bigquery.SchemaField("READING_nb", "FLOAT"),
    bigquery.SchemaField("WRITING_nb", "FLOAT"),
    bigquery.SchemaField("SPELLING_nb", "FLOAT"),
    bigquery.SchemaField("NUMERACY_nb", "FLOAT"),
    bigquery.SchemaField("GRAMMAR___PUNCTUATION_nb", "FLOAT"),
    bigquery.SchemaField("Class", "STRING"),
    bigquery.SchemaField("Date_of_Birth", "STRING"),
    bigquery.SchemaField("Gender", "STRING"),
    bigquery.SchemaField("LBOTE", "BOOLEAN"),
    bigquery.SchemaField("ATSI", "BOOLEAN"),
    bigquery.SchemaField("Home_School_Name", "STRING"),
    bigquery.SchemaField("Reporting_School_Name", "STRING"),
    bigquery.SchemaField("Cases_ID", "STRING"),
]
NAPLAN_CLUSTERING_FIELDS = ["APS_Year", "Reporting_Test", "Cases_ID", "Gender"]

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
