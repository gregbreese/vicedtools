import pandas as pd
import numpy as np
import re

import pandas as pd
import numpy as np
import glob
import re

class Reports:
    '''A container class for Compass Reports data.'''

    def __init__(self, data=None, class_details=None):
        columns = ['Time', 
                   'ClassCode', 
                   'StudentCode',
                   'ResultName',  
                   'ResultGrade', 
                   'ResultScore', 
                   'Type',
                   'SubjectCode',
                   'SubjectName', 
                   'LearningArea', 
                   'TeacherCode']
        self.data = pd.DataFrame(columns=columns)
        if type(data) == pd.core.frame.DataFrame:
            self.data = pd.concat([self.data,data], 
                                  ignore_index=True)
        columns = ['Time',
                   'ClassCode',
                   'TeacherCode']
        self.class_details = pd.DataFrame(columns=columns)
        if type(class_details) == pd.core.frame.DataFrame:
            self.class_details = pd.concat([self.class_details,class_details],
                                           ignore_index=True)
        
    @classmethod
    def fromReportsExport(cls,
                          filename, 
                          year=None, 
                          semester=None, 
                          grade_score_mapper=None, 
                          grade_dtype=None, 
                          replace_values=None):
        temp_df = pd.read_csv(filename, 
                              na_values=None, 
                              keep_default_na=False)
        temp_df = temp_df[temp_df["AssessmentType"] == "Work Habits"]    

        if not year:
            # attempt to determine year from filename
            year_pattern = "(?P<year>2[0-9][0-9][0-9])"
            m = re.search(year_pattern,filename)
            if m:
                year = m.group('year')
            else:
                raise ValueError("Could not determine year for reports export file.]n"
                                 "Try including the year in the filename.")
        if not semester:
            semester_pattern = "(?:[Ss][Ee][Mm][A-Za-z ]*)(?P<semester>[12]|[Oo]ne|[Tt]wo)"
            m = re.search(semester_pattern,filename)
            if m:
                semester = m.group('semester')
            else:
                raise ValueError("Could not determine semester for reports export file.\n"
                                 "Try including Sem 1, Sem 2 in the filenames.")              
        time = cls._semesterDateMapper(year, semester)
        temp_df["Time"] = time
        temp_df["Time"] = pd.to_datetime(temp_df["Time"])

        if replace_values:
            temp_df.replace(replace_values,inplace=True)
        if grade_dtype:
            temp_df["Result"] = temp_df["Result"].astype(grade_dtype)
            temp_df.dropna(subset=["Result"], inplace=True)
        if grade_score_mapper:
            temp_df["ResultScore"] = temp_df["Result"].apply(grade_score_mapper)
        else:
            temp_df["ResultScore"] = None
    
        temp_df.rename(columns={"Result":"ResultGrade", 
                                "AssessmentArea":"ResultName", 
                                "AssessmentType":"Type"}, 
                       inplace=True)
        
        temp_df["SubjectName"] = None
        temp_df["TeacherCode"] = None
        
        columns = ['Time', 
                   'ClassCode', 
                   'StudentCode',
                   'ResultName',  
                   'ResultGrade', 
                   'ResultScore', 
                   'Type',
                   'SubjectName', 
                   'TeacherCode']
        return cls(temp_df[columns])

    @classmethod
    def fromLearningTasksExport(cls,
                                filename, 
                                year=None, 
                                grade_score_mapper=None, 
                                grade_dtype=None, 
                                replace_values=None):
        temp_df = pd.read_csv(filename,
                              na_values=None, 
                              keep_default_na=False)
        temp_df = temp_df[temp_df["IsIncludedInReport"]]
        temp_df = temp_df[temp_df["ComponentType"] != "Comment"]
        temp_df = temp_df[temp_df["ReportCycleName"].isin(["Semester One", 
                                                           "Semester Two"])]

        if (not year):
            # attempt to determine year from filename
            year_pattern = "(?P<year>2[0-9][0-9][0-9])"
            m = re.search(year_pattern,filename)
            if m:
                year = m.group('year')
            else:
                raise ValueError("Could not determine year for Learning Tasks export file.")
        temp_df["Year"] = year
        temp_df["Time"] = temp_df.apply(lambda x: cls._semesterDateMapper(x["Year"], 
                                                                          x["ReportCycleName"]), 
                                        axis=1)
        temp_df['Time'] = pd.to_datetime(temp_df['Time'])
        
            
        temp_df["Type"] = "Academic" # differentiate from work habits
        
        if replace_values:
            temp_df.replace(replace_values,inplace=True)
        if grade_dtype:
            temp_df["Result"] = temp_df["Result"].astype(grade_dtype)
            temp_df.dropna(subset=["Result"], inplace=True)
        if grade_score_mapper:
            temp_df["ResultScore"] = temp_df["Result"].apply(grade_score_mapper)
        else:
            temp_df["ResultScore"] = None
        temp_df.rename(columns={'Code':'ClassCode', 
                                'TaskName':'ResultName', 
                                'Result':'ResultGrade', 
                                "TeacherImportIdentifier":"TeacherCode"}, 
                       inplace=True)
        class_details_columns = ['Time',
                                 'ClassCode',
                                 'TeacherCode']
        data_columns = ['Time', 
                   'ClassCode', 
                   'StudentCode',
                   'ResultName',  
                   'ResultGrade', 
                   'ResultScore', 
                   'Type',
                   'SubjectName', 
                   'TeacherCode']
        return cls(temp_df[data_columns],
                    temp_df[class_details_columns])
    
    @classmethod
    def fromProgressReportsExport(cls,
                                 filename, 
                                 progress_report_items, 
                                 year=None, 
                                 term=None, 
                                 grade_score_mapper=None, 
                                 grade_dtype=None, 
                                 replace_values=None):
        temp_df = pd.read_csv(filename, 
                              na_values=None, 
                              keep_default_na=False)
        temp_df.rename(columns={"Id":"StudentCode", 
                                "Subject":"ClassCode", 
                                "Teacher":"TeacherCode"}, 
                       inplace=True)

        # unpivot progress report items
        temp_df = temp_df.melt(id_vars=["StudentCode", 
                                        "ClassCode", 
                                        "TeacherCode"],
                               value_vars=progress_report_items,
                               var_name="ResultName",
                               value_name="ResultGrade")
        
        if not year:
            year_pattern = "(?P<year>2[0-9][0-9][0-9])"
            m = re.search(year_pattern,filename)
            if m:
                year = m.group('year')
            else:
                raise ValueError("Could not determine year from filename.")
        if not term:
            term_pattern = "(?:[Tt][Ee][Rr][A-Za-z ]*)(?P<term>[12])"
            m = re.search(term_pattern,filename)
            if m:
                term = m.group('term')
            else:
                raise ValueError("Could not determine term from filename.")
        time = cls._termDateMapper(year, term)
        temp_df["Time"] = time
        temp_df['Time'] = pd.to_datetime(temp_df['Time'])

        temp_df["Type"] = "Work Habits"

        if replace_values:
            temp_df.replace(replace_values,inplace=True)
        if grade_dtype:
            temp_df["ResultGrade"] = temp_df["ResultGrade"].astype(grade_dtype)
            temp_df.dropna(subset=["ResultGrade"], inplace=True)
        if grade_score_mapper:
            temp_df["ResultScore"] = temp_df["ResultGrade"].apply(grade_score_mapper)
        else:
            temp_df["ResultScore"] = None
        
        temp_df["SubjectName"] = None
        temp_df["TeacherCode"] = None
        
        class_details_columns = ['Time',
                                 'ClassCode',
                                 'TeacherCode']
        data_columns = ['Time', 
                       'ClassCode', 
                       'StudentCode',
                       'ResultName',  
                       'ResultGrade', 
                       'ResultScore', 
                       'Type',
                       'SubjectName', 
                       'TeacherCode']
        return cls(temp_df[data_columns],
                    temp_df[class_details_columns])
    
    @classmethod
    def _semesterDateMapper(cls, year, semester):
        if semester in ["Semester One", "1", "One", "one"]:
            return str(year) + "-06-30"
        elif semester in ["Semester Two", "2", "Two", "two"]:
            return str(year) + "-12-31"
        else:
            return str(year) + "-12-31"

    @classmethod
    def _termDateMapper(cls, year, term):
        if term in ["1", "One", "one"]:
            return str(year)  + "-03-31"
        elif term in ["2", "Two", "two"]:
            return str(year) + "-06-30"
        elif term in ["3", "Three", "three"]:
            return str(year) + "-09-30"
        elif term in ["4", "Four", "four"]:
            return str(year) + "-12-31"
        else:
            return None

    def addLearningTasksExport(self,
                               filename, 
                               grade_score_mapper=None, 
                               grade_dtype=None, 
                               replace_values=None):
        temp = Reports.fromLearningTasksExport(filename, 
                                               grade_score_mapper=grade_score_mapper, 
                                               grade_dtype=grade_dtype, 
                                               replace_values=replace_values)
        self.data = pd.concat([self.data, temp.data],
                                        ignore_index=True)
        self.data.drop_duplicates(subset=["Time",
                                          "StudentCode",
                                          "ClassCode",
                                          "ResultName"],
                                  inplace=True)
        self.class_details = pd.concat([self.class_details, temp.class_details],
                                       ignore_index=True)
        self.class_details.drop_duplicates(inplace=True)

    def addReportsExport(self,
                         filename, 
                         grade_score_mapper=None, 
                         grade_dtype=None, 
                         replace_values=None):
        temp = Reports.fromReportsExport(filename, 
                                           grade_score_mapper=grade_score_mapper, 
                                           grade_dtype=grade_dtype, 
                                           replace_values=replace_values)
        self.data = pd.concat([self.data, temp.data],
                              ignore_index=True)
        self.data.drop_duplicates(subset=["Time",
                                          "StudentCode", 
                                          "ClassCode",
                                          "ResultName"],
                                  inplace=True)

    def addProgressReportsExport(self,
                                 filename, 
                                 progress_report_items, 
                                 grade_score_mapper=None, 
                                 grade_dtype=None, 
                                 replace_values=None):
        temp = Reports.fromProgressReportsExport(filename,
                                         progress_report_items,
                                         grade_score_mapper=grade_score_mapper,
                                         grade_dtype=grade_dtype,
                                         replace_values=replace_values)
        self.data = pd.concat([self.data, temp.data],
                              ignore_index=True)
        self.data.drop_duplicates(subset=["Time",
                                          "StudentCode", 
                                          "ClassCode",
                                          "ResultName"],
                                  inplace=True)
        self.class_details = pd.concat([self.class_details, temp.class_details],
                                       ignore_index=True)
        self.class_details.drop_duplicates(inplace=True)

    def __add__(self,other):
        data = pd.concat([self.data, other.data],
                                        ignore_index=True)
        data.drop_duplicates(subset=["Time",
                                     "StudentCode", 
                                     "ClassCode",
                                     "ResultName"],
                             inplace=True)
        return Reports(data)
    
    def importSubjectsData(self,
                          subjects_file,
                          class_code_parser,
                          replace_values=None):

        subjects_df = pd.read_csv(subjects_file)

        subjects = subjects_df["SubjectCode"].values
        pattern_string = "(?P<code>" + "|".join(subjects) + ")"

        self.data["SubjectCode"] = self.data["ClassCode"].apply(class_code_parser, 
                                                                pattern_string=pattern_string)
        if replace_values:
            self.data.replace(replace_values, inplace=True)
        columns = ['Time', 
                   'ClassCode', 
                   'StudentCode',
                   'ResultName',  
                   'ResultGrade', 
                   'ResultScore', 
                   'Type',
                   'SubjectCode',
                   'TeacherCode']
        self.data = pd.merge(self.data[columns], 
                             subjects_df,
                             how="left",
                             on="SubjectCode")

    def updateFromClassDetails(self):
        self.data.drop(columns="TeacherCode", 
                       inplace=True, 
                       errors="ignore")
        self.data = pd.merge(self.data, 
                             self.class_details,
                             how="left",
                             on=["Time",
                                 "ClassCode"])
    
    def summary(self):
        grpd = self.data.groupby(['Time',
                                  'ClassCode',
                                  'StudentCode',
                                  'Type',
                                  'SubjectCode',
                                  'SubjectName',
                                  'LearningArea',
                                  'TeacherCode'],
                                 as_index=False).mean()
        pvtd = grpd.pivot_table(index=['Time',
                                       'ClassCode',
                                       'StudentCode',
                                       'SubjectCode',
                                       'SubjectName',
                                       'LearningArea',
                                       'TeacherCode'],
                                columns=["Type"],
                                values="ResultScore").reset_index()
        pvtd.sort_values("Time",
                         ascending=False,
                         inplace=True)
        return pvtd

    def saveReports(self, filename):
        self.data.to_csv(filename, index=False)
    
    def saveSummary(self, filename):
        summary = self.summary()
        summary.to_csv(filename, index=False)
