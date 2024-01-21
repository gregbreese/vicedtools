#!/usr/bin/env python

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
"""Executable script for combining VCE exports into single files."""

import glob
import os
import re

import pandas as pd

from vicedtools.scripts.config import (vass_student_details_dir,
                                         vass_school_program_dir, 
                                         vass_external_scores_dir, 
                                         vass_gat_scores_dir, 
                                         vass_school_scores_dir, 
                                         vass_predicted_scores_dir, 
                                         vass_moderated_coursework_scores_dir, 
                                         vass_dir)


def main():
    # aggregate student details
    files = glob.glob(os.path.join(vass_student_details_dir, "personal details summary *.csv"))

    student_details_df = pd.DataFrame()
    for f in files:
        temp_df = pd.read_csv(f, dtype=str)
        
        pattern = "personal details summary ([0-9]{4}).csv"
        m = re.findall(pattern, f)
        if m:
            year = m[0]
            temp_df["Year"] = year
            student_details_df = pd.concat([student_details_df,temp_df])
    student_details_df.fillna("", inplace=True)
    student_details_df.rename(columns={"Family Name":"Surname", "First Name":"FirstName"}, inplace=True)

    # aggregate school scores
    files = glob.glob(os.path.join(vass_school_scores_dir, "school scores *.csv"))

    school_scores_df = pd.DataFrame()
    for f in files:
        temp_df = pd.read_csv(f, dtype=str)
        
        pattern = "school scores ([0-9]{4}).csv"
        m = re.findall(pattern, f)
        if m:
            year = m[0]
            temp_df["Year"] = year
            school_scores_df = pd.concat([school_scores_df,temp_df])
    school_scores_df["Result Percentage"] = school_scores_df["Result"].astype(float) / school_scores_df["Max Score"].astype(int)
    cols = ['Year', 'Student Number', 'Student Name', 'Unit Code', 'Unit Name', 'GA', 
            'Focus Area', 'Class', 'Result', 'Max Score', "Result Percentage", 'SIAR', 'SIARScore', 'SIAR Max Score', ]
    school_scores_df["Student Name"] = school_scores_df["Student Name"].str.strip()

    files = glob.glob(os.path.join(vass_moderated_coursework_scores_dir, "moderated coursework scores *.csv"))

    # Aggregate moderated score data
    moderated_scores_df = pd.DataFrame()
    for f in files:
        temp_df = pd.read_csv(f, dtype=str)
        
        pattern = "moderated coursework scores ([0-9]{4}).csv"
        m = re.findall(pattern, f)
        if m:
            year = m[0]
            temp_df["Year"] = year
            moderated_scores_df = pd.concat([moderated_scores_df,temp_df])
    moderated_scores_df["Subject"] = moderated_scores_df["Subject"].replace({"MATHEMATICAL METHODS":"MATHS: MATHEMATICAL METHODS", 
                                                                            "FURTHER MATHEMATICS": "MATHS: FURTHER MATHEMATICS", 
                                                                            "SPECIALIST MATHEMATICS": "MATHS: SPECIALIST MATHEMATICS", 
                                                                            "FRENCH": "LANGUAGES: FRENCH",
                                                                            "CHINESE FIRST LANGUAGE": "LANGUAGES: CHINESE FIRST LANGUAGE"})
    moderated_scores_df["GA"] = moderated_scores_df["GA Number"].astype(str) + " - " + moderated_scores_df["GA Name"]

    school_scores_df = pd.merge(school_scores_df, moderated_scores_df, left_on=["Year", "Unit Name", "GA", "Result"], right_on=["Year", "Subject", "GA", "School score"], how='left')

    rows = school_scores_df["Unit Name"].str[:5] == "MATHS"
    school_scores_df.loc[rows,"Unit Name"] = school_scores_df.loc[rows,"Unit Name"].str[7:]
    rows = school_scores_df["Unit Name"].str[:9] == "LANGUAGES"
    school_scores_df.loc[rows,"Unit Name"] = school_scores_df.loc[rows,"Unit Name"].str[11:]
    school_scores_df["Unit Name"] = school_scores_df["Unit Name"].str.title()
    school_scores_df["Unit Name"].replace({"English (Eal)":"English (EAL)", 
        "Algorithmics (Hess)":"Algorithmics (HESS)", 
        "Health And Human Development":"Health and Human Development",
        "Applied Comp: Software Development": "Applied Computing: Software Development",
        "Computing: Software Development": "Applied Computing: Software Development",
        "Software Development": "Applied Computing: Software Development",
        "Chinese Second Lang. Adv.":"Chinese Second Language Advanced",
        "History: Revolutions":"History Revolutions",
        "Mathematical Methods (Cas)":"Mathematical Methods",
        "Food And Technology":"Food Studies",
        "Computing: Informatics":"Applied Computing: Data Analytics"
        }, inplace=True)
    
    cols = ['Year', 'Student Number', 'Student Name', 'Focus Area', 'Class', 'Result',
       'Max Score', 'SIAR', 'SIAR Max Score', 'Unit', 'GA', 'SIARScore',
       'Unit Code', 'Unit Name', 'Result Percentage', 'School score', 'Moderated score']
    filename = os.path.join(vass_dir, "school scores.csv")
    school_scores_df[cols].to_csv(filename, index=False)

    # Aggregate GAT scores
    files = glob.glob(os.path.join(vass_gat_scores_dir, "gat scores *.csv"))

    gat_scores_df = pd.DataFrame()
    for f in files:
        temp_df = pd.read_csv(f)
        
        pattern = "gat scores ([0-9]{4}).csv"
        m = re.findall(pattern, f)
        if m:
            year = m[0]
            temp_df["Year"] = year
            
            gat_scores_df = pd.concat([gat_scores_df,temp_df])

    #gat_scores_df.rename(columns={"loginYear":"Year"}, inplace=True)

    student_details_cols = ['Student Number', 'Year', 'Year Level']

    gat_scores_df = pd.merge(gat_scores_df, student_details_df[student_details_cols].rename(columns={"Student Number":"candNum"}), on=["candNum", "Year"])


    cols = ['Year', 'candNum', 'Student Name', 'stdCOM', 'stdAHU', 'stdMST', "Year Level"]
    filename = os.path.join(vass_dir, "gat scores.csv")
    gat_scores_df[cols].to_csv(filename, index=False)

    # Aggregate external scores
    files = glob.glob(os.path.join(vass_external_scores_dir, "external scores *.csv"))

    external_scores_df = pd.DataFrame()
    for f in files:
        temp_df = pd.read_csv(f, dtype=str)
        
        pattern = "external scores ([0-9]{4}).csv"
        m = re.findall(pattern, f)
        if m:
            year = m[0]
            temp_df["Year"] = year
            external_scores_df = pd.concat([external_scores_df,temp_df])
    external_scores_df["Unit Name"] = external_scores_df["Unit Name"].str[:-1].str.strip()
    external_scores_df.drop_duplicates(subset=["Unit Name", "Student Number"], inplace=True)

    external_scores_df["Study Score*"] = external_scores_df["Study Score"].replace(to_replace="UN", value="NaN").replace(to_replace="wh", value="NaN").replace(to_replace="nan", value="NaN")
    external_scores_df["Study Score*"] = external_scores_df["Study Score*"].astype("float64")

    column_map = {"Unit Name": "UnitName",
                "Unit Code":"UnitCode",
                "Teacher Code":"TeacherCode",
                "Teacher Name":"TeacherName",
                "Class Code":"ClassCode",
                "Year Level":"YearLevel",
                "Form Group":"FormGroup",
                "Student Number":"StudentNumber",
                "Student Name":"StudentName"
                }

    external_scores_df.rename(columns=column_map, inplace=True)

    filename = os.path.join(vass_dir, "external scores.csv")
    external_scores_df.to_csv(filename, index=False)

    files = glob.glob(os.path.join(vass_predicted_scores_dir, "predicted scores *.csv"))

    # aggregate predicted scores
    predicted_scores_df = pd.DataFrame()
    for f in files:
        temp_df = pd.read_csv(f, dtype=str)
        
        pattern = "predicted scores ([0-9]{4}).csv"
        m = re.findall(pattern, f)
        if m:
            year = m[0]
            temp_df["Year"] = year
            predicted_scores_df = pd.concat([predicted_scores_df,temp_df])
        
    student_details_cols = ['Student Number', 'Surname', 'FirstName', 'External ID', 'Gender', 'Year']
    predicted_scores_df = predicted_scores_df.merge(student_details_df[student_details_cols], on=["Year", "Surname", "FirstName"])
    predicted_scores_df["ClassGroup"] = predicted_scores_df["ClassGroup"].str.strip()

    files = glob.glob(os.path.join(vass_school_program_dir, "school program summary *.csv"))
    student_program_df = pd.DataFrame()
    for f in files:
        temp_df = pd.read_csv(f, dtype=str)
        
        pattern = "school program summary ([0-9]{4}).csv"
        m = re.findall(pattern, f)
        if m:
            year = m[0]
            temp_df["Year"] = year
            student_program_df = pd.concat([student_program_df,temp_df])
    student_program_df.fillna("", inplace=True)

    rows = student_program_df["Unit Name"].str[-1] == '4'
    student_program_df = student_program_df.loc[rows]

    student_program_df["Subject"] = student_program_df["Unit Name"].str[:-2]

    rows = student_program_df["Subject"].str[:5] == "MATHS"
    student_program_df.loc[rows,"Subject"] = student_program_df.loc[rows,"Subject"].str[7:]
    rows = student_program_df["Subject"].str[:9] == "LANGUAGES"
    student_program_df.loc[rows,"Subject"] = student_program_df.loc[rows,"Subject"].str[11:]
    student_program_df["Subject"] = student_program_df["Subject"].str.title()
    student_program_df["Subject"].replace({"English (Eal)":"English (EAL)", 
        "Algorithmics (Hess)":"Algorithmics (HESS)", 
        "Health And Human Development":"Health and Human Development",
        "Applied Comp: Software Development": "Applied Computing: Software Development",
        "Computing: Software Development": "Applied Computing: Software Development",
        "Software Development": "Applied Computing: Software Development",
        "Chinese Second Lang. Adv.":"Chinese Second Language Advanced",
        "History: Revolutions":"History Revolutions",
        "Mathematical Methods (Cas)":"Mathematical Methods",
        "Food And Technology":"Food Studies",
        "Computing: Informatics":"Applied Computing: Data Analytics"
        }, inplace=True)

    student_program_df.rename(columns={"Class Code":"ClassGroup"}, inplace=True)
    student_program_df["ClassGroup"] = student_program_df["ClassGroup"].str.strip()
    filename = os.path.join(vass_dir, "student programs.csv")
    student_program_df.to_csv(filename, index=False)

    student_program_cols = ['Year', 'ClassGroup', 'Subject', 'Teacher Code', 'Teacher Name']
    predicted_scores_df = predicted_scores_df.merge(student_program_df[student_program_cols], on=["Year", "Subject", "ClassGroup"], how='left')

    column_map = {"Surname":"Last Name",
                "FirstName":"First Name",
                "YearLevel":"Year Level",
                "ClassGroup":"Class",
                "External ID":"StudentCode",
                "Teacher Code":"Teacher"}
    predicted_scores_df.rename(columns=column_map, inplace=True)

    filename = os.path.join(vass_dir, "predicted scores.csv")
    predicted_scores_df.to_csv(filename, index=False)


if __name__ == "__main__":
    main()
