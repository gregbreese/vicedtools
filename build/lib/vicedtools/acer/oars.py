import pandas as pd
import numpy as np
import re
from datetime import datetime

# need to add customisable maths/english class code patterns
def class_selector(class_string):
    '''Identifies whether a given class name is an english or maths class.

    Keyword arguments
    class_string: a class code string
    '''
    # maths pattern
    pattern = "(?P<class_code>[789]MA[BEFG][0-9]|10MA[PQRSTU][X]?[0-9]|11FM[PQRSTU][0-9])"
    match = re.match(pattern,  class_string)
    if match:
        class_code = match.group("class_code")
        return pd.Series(["Maths", class_code])
    # english/eal pattern
    pattern = "(?P<class_code>[789]EN[BEFG][0-9]|10EN[PQRSTU][0-9]|[789]EAL[BEFG][0-9]?|10EAL[PQRSTU][0-9]?)"
    match = re.match(pattern,  class_string)
    if match:
        class_code = match.group("class_code")
        return pd.Series(["English", class_code])
    # else
    return pd.Series([None,None])

def student_imports(student_details_file, 
                    student_enrolment_file, 
                    current_students_file, 
                    new_students_file, 
                    update_students_file):
    '''Creates files to update the OARS student database.

    Creates two separate files, one to update the details of existing students
    in the database and one to add new students.

    Keyword arguments
    student_details_file: a student details export csv from Compass. Can be 
        downloaded using vicedtools.compass.export_student_details or directly
        from https://###.compass.education/Services/FileDownload/CsvRequestHandler?type=37
    student_enrolment_file: a student enrolment file exported from Compass.
        Can be downloaded using vicedtools.compass.export_student_enrolments
    current_students_file: a current students export from OARS
    new_students_file: the filename to save the new students import for OARS
    update_students_file: the filename to save the update students import for OARS
    '''
    existing_students_df = pd.read_excel(current_students_file)
    student_details_df = pd.read_csv(student_details_file, dtype=np.str)
    student_enrolment_df = pd.read_csv(student_enrolment_file)

    # create new student details columns
    # columns needed
    # System ID, Family name, Given name, Middle names, Username, Password,
    # Date of birth, Gender Tags, Unique ID, Enrolled, Year level, School year
    student_details_df.rename(columns={"Last Name":"Family name", 
                                        "Preferred Name":"Given name",
                                        "SUSSI ID":"Username",
                                        "Year Level":"Year level"}, 
                                        inplace=True, 
                                        errors="raise")
    # column formatting
    student_details_df["Family name"] = student_details_df["Family name"].str.title()
    student_details_df["Date of birth"] = pd.to_datetime(student_details_df["Date of birth"], 
                                                            format="%d/%m/%Y") 
    student_details_df["Date of birth"] = student_details_df["Date of birth"].dt.strftime("%d-%m-%Y")
    # select relevant columns
    columns = ["Family name", "Given name", "Username", "Date of birth", 
                "Gender", "Year level", "Form Group"]
    student_details_df = student_details_df[columns]
    # create other columns
    student_details_df["Middle names"] = ""
    student_details_df["Password"] = student_details_df["Date of birth"]
    student_details_df["Unique ID"] = student_details_df["Username"]
    student_details_df["School year"] = datetime.today().stftime('%Y')
    student_details_df["Enrolled"] = "Enrolled"
        
    student_enrolment_df[["Subject", "Class code"]] = student_enrolment_df["Section SIS ID"].apply(class_selector)
    student_enrolment_df.dropna(subset=["Subject"],  inplace=True)
    # remove multiple enrolments (keep most recent)
    student_enrolment_df.drop_duplicates(subset=["SIS ID", "Subject"], 
                                                    keep="last", 
                                                    inplace=True)
    # pivot to create english and maths columns
    student_enrolment_df = student_enrolment_df.pivot(index="SIS ID", 
                                                        columns="Subject", 
                                                        values="Class code").reset_index()
    student_enrolment_df.rename(columns={"SIS ID":"Username"}, inplace=True)
    # merge with student details and create class tag string
    student_details_df = student_details_df.merge(student_enrolment_df, on="Username")
    student_details_df["Tags"] = (student_details_df["Form Group"] 
                                    + "," + student_details_df["English"] 
                                    + "," + student_details_df["Maths"]
                                )                       
                                                
                                                
    # check existing list and unenrol exited students+
    #oars_df["Date of birth"] = pd.to_datetime(oars_df["Date of birth"])
    #oars_df["Password"] = oars_df["Date of birth"]
    students_to_unenrol = pd.DataFrame(existing_students_df[~existing_students_df["Username"].isin(student_details_df["Username"])])
    students_to_unenrol["Enrolled"] = "Unenrolled"
    students_to_unenrol["Tags"] = ""

    student_details_df = student_details_df.merge(existing_students_df[["System ID", "Username"]], 
                                                    on="Username", 
                                                    how="left")
    student_details_df.fillna("", inplace=True)

    columns = ["System ID", "Family name", "Given name", "Middle names", 
                "Username", "Password", "Date of birth", "Gender", "Tags", 
                "Unique ID", "Enrolled", "Year level", "School year"]
    export_df = pd.concat([student_details_df[columns],students_to_unenrol])
    export_df = export_df[columns]

    # separate exports for new students and updating existing students
    export_df[export_df["System ID"] != ""].to_excel(update_students_file, 
                                                        index=False)
    new_student_columns = ["Family name", "Given name", "Middle names", 
                            "Username", "Password", "Date of birth", "Gender",
                            "Tags", "Unique ID", "Year level", "School year"]
    export_df[export_df["System ID"] == ""][new_student_columns].to_excel(new_students_file, 
                                                                            "Sheet1",  
                                                                            index=False)